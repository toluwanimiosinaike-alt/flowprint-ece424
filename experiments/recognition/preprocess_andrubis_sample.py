import argparse
import csv
import glob
import gzip
import json
import os
import pickle
import shutil
import sys
import subprocess
import tempfile
import tarfile
from collections import defaultdict

import numpy as np
from cryptography import x509


def extract_capture(archive, member, destination):
    raw_member = archive.extractfile(member)
    if raw_member is None:
        raise OSError("Unable to read archive member {}".format(member.name))

    with raw_member, gzip.GzipFile(fileobj=raw_member) as pcap_stream:
        with open(destination, "wb") as output_file:
            shutil.copyfileobj(pcap_stream, output_file)


def preprocess_with_scapy(captures, stats):
    from scapy.layers.inet import IP, TCP, UDP
    from scapy.layers.inet6 import IPv6
    from scapy.utils import PcapReader

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, os.path.join(root, "flowprint"))
    from flows import Flow

    all_flows = []
    labels = []
    for path, app_hash in captures:
        flows = {}
        stream_ids = {}
        reader = PcapReader(path)
        try:
            for packet in reader:
                stats["packets"] += 1
                ip = packet.getlayer(IP) or packet.getlayer(IPv6)
                if ip is None:
                    continue
                if packet.haslayer(TCP):
                    transport = packet[TCP]
                    protocol = "tcp"
                elif packet.haslayer(UDP):
                    transport = packet[UDP]
                    protocol = "udp"
                else:
                    continue

                src = str(ip.src)
                dst = str(ip.dst)
                src_port = int(transport.sport)
                dst_port = int(transport.dport)
                endpoints = tuple(sorted(((src, src_port), (dst, dst_port))))
                stream_key = (protocol, endpoints)
                if stream_key not in stream_ids:
                    stream_ids[stream_key] = len(stream_ids)
                stream_id = stream_ids[stream_key]

                flow = flows.setdefault(stream_id, Flow())
                flow.add([
                    path, protocol, stream_id, float(packet.time), len(packet),
                    src, dst, src_port, dst_port, None,
                ])
        finally:
            reader.close()
        all_flows.extend(flows.values())
        labels.extend([app_hash] * len(flows))
        stats["flows"] += len(flows)

    X = np.empty(len(all_flows), dtype=object)
    X[:] = all_flows
    y = np.asarray(labels, dtype=object)
    return X, y


def preprocess_with_tshark(captures, stats):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, os.path.join(root, "flowprint"))
    from flows import Flow

    fields = (
        "frame.time_epoch", "tcp.stream", "udp.stream", "ip.proto",
        "ip.src", "ipv6.src", "tcp.srcport", "udp.srcport",
        "ip.dst", "ipv6.dst", "tcp.dstport", "udp.dstport",
        "frame.len", "tls.handshake.certificate",
    )

    all_flows = []
    labels = []
    for path, app_hash in captures:
        try:
            command = ["tshark", "-r", path, "-T", "fields",
                       "-E", "separator=\t", "-E", "occurrence=f"]
            for field in fields:
                command.extend(["-e", field])
            completed = subprocess.run(
                command, capture_output=True, check=True)
            flows = {}
            for row in completed.stdout.decode(
                    "utf-8", "replace").splitlines():
                values = row.split("\t")
                if len(values) != len(fields):
                    raise ValueError(
                        "TShark returned {} fields; expected {}.".format(
                            len(values), len(fields)))

                timestamp, tcp_stream, udp_stream, ip_protocol = values[:4]
                src = values[4] or values[5]
                src_port = values[6] or values[7]
                dst = values[8] or values[9]
                dst_port = values[10] or values[11]
                length = values[12]
                certificate = values[13]
                protocol = {"6": "tcp", "17": "udp"}.get(ip_protocol)
                if not protocol or not src or not dst or \
                        not src_port or not dst_port or not timestamp or \
                        not length:
                    continue

                stream_id = tcp_stream if protocol == "tcp" else udp_stream
                if not stream_id:
                    stream_id = repr((src, src_port, dst, dst_port))
                serial = None
                if certificate:
                    der = bytes.fromhex(certificate.split(",")[0].replace(
                        ":", ""))
                    serial = x509.load_der_x509_certificate(der).serial_number

                key = (protocol, stream_id)
                flow = flows.setdefault(key, Flow())
                flow.add([
                    path, protocol, stream_id, float(timestamp), int(length),
                    src, dst, int(src_port), int(dst_port), serial,
                ])

            all_flows.extend(flows.values())
            labels.extend([app_hash] * len(flows))
            stats["captures_read"] += 1
            stats["packets"] += len(completed.stdout.splitlines())
        except Exception as error:
            stats["capture_errors"] += 1
            stats["errors"].append("{}: {}: {}".format(
                os.path.basename(path), type(error).__name__, error))

    X = np.empty(len(all_flows), dtype=object)
    X[:] = all_flows
    y = np.asarray(labels, dtype=object)
    stats["flows"] = len(X)
    return X, y


def write_vt_csv(path, reports):
    if not reports:
        return None
    output_path = os.path.splitext(path)[0] + "_virustotal.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=("apk_hash", "positives", "total", "scan_date"))
        writer.writeheader()
        for app_hash, report in sorted(reports.items()):
            writer.writerow({"apk_hash": app_hash, **report})
    return output_path


def find_tshark(configured_path=None):
    executable = shutil.which(configured_path or "tshark")
    if configured_path and executable is None and \
            os.path.isfile(configured_path):
        executable = os.path.abspath(configured_path)
    if executable is None:
        if configured_path:
            raise FileNotFoundError(
                "Configured TShark executable was not found: {}".format(
                    configured_path))
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", ""),
                         "Wireshark", "tshark.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""),
                         "Wireshark", "tshark.exe"),
        ]
        executable = next((path for path in candidates if os.path.isfile(path)),
                          None)
    if executable:
        directory = os.path.dirname(executable)
        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
    return executable


def collect_archive(path, max_apps, max_captures_per_app, temp_dir, stats):
    result = []
    selected_apps = set()
    current_app = None
    captures_for_app = 0
    with tarfile.open(path, "r|gz") as archive:
        for member in archive:
            parts = member.name.split("/")
            if not member.isfile() or not member.name.endswith(".dump.gz") or \
                    len(parts) != 5:
                continue
            app_hash = parts[3]
            if app_hash != current_app:
                if len(selected_apps) >= max_apps:
                    break
                current_app = app_hash
                selected_apps.add(app_hash)
                stats["apps_seen"] += 1
                captures_for_app = 0
            if max_captures_per_app and \
                    captures_for_app >= max_captures_per_app:
                continue
            try:
                capture_name = os.path.basename(member.name)[:-len(".dump.gz")]
                destination = os.path.join(
                    temp_dir, "{}_{}.pcap".format(app_hash, capture_name))
                extract_capture(archive, member, destination)
                result.append((destination, app_hash))
                stats["pcaps_read"] += 1
                captures_for_app += 1
            except Exception as error:
                stats["pcap_errors"] += 1
                stats["errors"].append("{}: {}: {}".format(
                    member.name, type(error).__name__, error))
    stats["apps_with_flows"] = len({label for _, label in result})
    return result


def load_vt_reports(path, app_hashes):
    reports = {}
    errors = []
    if not app_hashes:
        return reports, errors
    try:
        with tarfile.open(path, "r|gz") as archive:
            for member in archive:
                if not member.isfile() or not member.name.endswith(".vt"):
                    continue
                app_hash = os.path.basename(member.name)[:-3]
                if app_hash not in app_hashes:
                    continue
                try:
                    raw = archive.extractfile(member)
                    if raw is None:
                        raise OSError("Unable to read archive member")
                    with raw:
                        report = json.load(raw)
                    reports[app_hash] = {
                        "positives": report.get("positives"),
                        "total": report.get("total"),
                        "scan_date": report.get("scan_date"),
                    }
                except Exception as error:
                    errors.append("{}: {}: {}".format(
                        member.name, type(error).__name__, error))
                if reports.keys() >= app_hashes:
                    break
    except (EOFError, tarfile.ReadError) as error:
        errors.append("VirusTotal archive ended unexpectedly: {}: {}".format(
            type(error).__name__, error))
    return reports, errors


def resolve_input_archives(args, parser):
    user_data_dir = os.path.abspath(args.user_data_dir)
    explicit_pcaps = any(
        (args.pcaps_a, args.pcaps_f, args.pcaps_extra))

    if explicit_pcaps:
        pcap_archives = []
        if args.pcaps_a:
            pcap_archives.append(("pcaps_a", args.pcaps_a))
        if args.pcaps_f:
            pcap_archives.append(("pcaps_f", args.pcaps_f))
        pcap_archives.extend(
            (os.path.basename(path), path) for path in args.pcaps_extra)
    else:
        if not os.path.isdir(user_data_dir):
            parser.error("User-data folder does not exist: {}".format(
                user_data_dir))
        paths = sorted(glob.glob(os.path.join(user_data_dir, "pcaps*.tar.gz")))
        pcap_archives = [
            (os.path.basename(path), path) for path in paths
        ]
        if not pcap_archives:
            parser.error(
                "No pcaps*.tar.gz archives found in {}. Add the PCAP "
                "archives there or pass --pcaps-a/--pcaps-f/--pcaps-extra."
                .format(user_data_dir))

    virustotal = args.virustotal or os.path.join(
        user_data_dir, "virustotal.tar.gz")
    for _, path in pcap_archives + [("virustotal", virustotal)]:
        if not os.path.isfile(path):
            parser.error("Input archive does not exist: {}".format(path))
    return pcap_archives, virustotal


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stream a bounded Andrubis pcap subset into FlowPrint flows.")
    default_user_data_dir = os.path.join(os.path.dirname(__file__), "user_data")
    default_output = os.path.join(
        os.path.dirname(__file__), "results", "member_b_user_data_flows.p")
    parser.add_argument(
        "--user-data-dir", default=default_user_data_dir,
        help="Folder containing PCAP archives and virustotal.tar.gz "
             "(default: {}).".format(default_user_data_dir))
    parser.add_argument("--pcaps-a",
                        help="Explicit pcaps_a archive; overrides discovery.")
    parser.add_argument("--pcaps-f",
                        help="Explicit pcaps_f archive; overrides discovery.")
    parser.add_argument("--pcaps-extra", nargs="*", default=[],
                        help="Additional explicit PCAP archives; when no "
                             "PCAP paths are given, all pcaps*.tar.gz files "
                             "in --user-data-dir are discovered.")
    parser.add_argument("--virustotal",
                        help="Explicit VirusTotal archive (default: "
                             "virustotal.tar.gz in --user-data-dir).")
    parser.add_argument("--tshark",
                        help="TShark executable or path; by default the "
                             "script searches PATH and common Windows paths.")
    parser.add_argument("--output", default=default_output,
                        help="Output pickle containing (flows, labels) "
                             "(default: {}).".format(default_output))
    parser.add_argument("--max-apps-per-archive", type=int, default=8)
    parser.add_argument("--max-captures-per-app", type=int, default=0,
                        help="Maximum captures extracted for each APK hash "
                             "in each archive; 0 means no per-app limit.")
    args = parser.parse_args(argv)
    if args.max_apps_per_archive < 1:
        parser.error("--max-apps-per-archive must be positive.")
    if args.max_captures_per_app < 0:
        parser.error("--max-captures-per-app cannot be negative.")

    pcap_archives, virustotal = resolve_input_archives(args, parser)
    print("PCAP archives: {}".format(
        ", ".join(path for _, path in pcap_archives)))
    print("VirusTotal archive: {}".format(virustotal))
    captures = []
    archive_stats = {}

    with tempfile.TemporaryDirectory(prefix="flowprint-member-b-") as temp_dir:
        for name, path in pcap_archives:
            stats = defaultdict(int)
            stats["errors"] = []
            captures.extend(collect_archive(
                path, args.max_apps_per_archive,
                args.max_captures_per_app, temp_dir, stats))
            archive_stats[name] = dict(stats)

        if not captures:
            raise RuntimeError("No pcap members were extracted from the archives.")

        tshark = find_tshark(args.tshark)
        if tshark:
            print("Preprocessing with the NDSS Reader and TShark: {}".format(
                tshark))
            parse_stats = defaultdict(int)
            parse_stats["errors"] = []
            X, y = preprocess_with_tshark(captures, parse_stats)
            print("TShark captures={}, packets={}, TCP/UDP flows={}, "
                  "capture_errors={}".format(
                      parse_stats.get("captures_read", 0),
                      parse_stats.get("packets", 0),
                      parse_stats.get("flows", 0),
                      parse_stats.get("capture_errors", 0)))
            for error in parse_stats.get("errors", []):
                print("PCAP ERROR: {}".format(error))
        else:
            print("TShark unavailable; preprocessing with Scapy fallback. "
                  "TLS certificate serials will be None.")
            parse_stats = defaultdict(int)
            X, y = preprocess_with_scapy(captures, parse_stats)
            print("Scapy packets={}, TCP/UDP flows={}".format(
                parse_stats.get("packets", 0), parse_stats.get("flows", 0)))

        if len(X) == 0:
            raise RuntimeError(
                "FlowPrint preprocessing produced no flows; check the run "
                "log and parser errors.")

        output_parent = os.path.dirname(os.path.abspath(args.output))
        os.makedirs(output_parent, exist_ok=True)
        with open(args.output, "wb") as output_file:
            pickle.dump((X, y), output_file, protocol=pickle.HIGHEST_PROTOCOL)

    app_hashes = {label for _, label in captures}
    vt_reports, vt_errors = load_vt_reports(virustotal, app_hashes)
    print("Preprocessed {} flows from {} APK hashes into {}".format(
        len(X), len(set(y)), os.path.abspath(args.output)))
    print("PCAP captures extracted: {}".format(len(captures)))
    for name, stats in archive_stats.items():
        print("{}: apps_seen={}, pcaps_extracted={}, pcap_errors={}".format(
            name, stats.get("apps_seen", 0),
            stats.get("pcaps_read", 0), stats.get("pcap_errors", 0)))
        for error in stats.get("errors", []):
            print("PCAP ERROR: {}".format(error))
    print("VirusTotal: {} of {} selected APK reports found; {} report errors"
          .format(len(vt_reports), len(app_hashes), len(vt_errors)))
    for app_hash, report in sorted(vt_reports.items()):
        print("VT {} positives={}/{} scan_date={}".format(
            app_hash, report["positives"], report["total"], report["scan_date"]))
    for error in vt_errors:
        print("VT ERROR: {}".format(error))
    vt_csv = write_vt_csv(args.output, vt_reports)
    if vt_csv:
        print("VirusTotal annotations written to {}".format(vt_csv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
