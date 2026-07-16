#!/usr/bin/env python3
"""Pipes the RoboMaster EP's raw H.264 video stream to stdout.

Not a ROS2 node - deliberately has no rclpy dependency, same spirit as
connection_test.cpp: a standalone diagnostic that talks the plaintext
SDK directly. Meant to be piped into a decoder, not used standalone:

    ros2 run robomaster_driver stream_view.py | ffplay -f h264 -probesize 32 -i -

What it does:
  1. Connects to the control port (40923), enters SDK mode ("command;").
  2. Sends "stream on;" to start the video feed.
  3. Connects to the video port (40921) and copies raw bytes to stdout
     until interrupted.
  4. On exit (Ctrl+C), sends "stream off;" and disconnects cleanly.

CAUTION: the control port only accepts one client connection at a time.
Don't run this alongside `make tether` (the ros2_control hardware
interface holds that same connection) - one will fail to connect.

IP comes from the ROBOMASTER_IP env var (set via .env / docker-compose),
same as connection_test.cpp, so there's still only one place to change it.
"""
import os
import signal
import socket
import sys

CONTROL_PORT = 40923
VIDEO_PORT = 40921
RECV_CHUNK = 4096


def send_and_expect(sock: socket.socket, cmd: str, expect: str = "ok") -> None:
    sock.sendall((cmd + ";").encode("utf-8"))
    resp = sock.recv(256).decode("utf-8", errors="replace").strip(";\r\n")
    if resp != expect:
        raise RuntimeError(f"'{cmd}' failed: expected '{expect}', got '{resp}'")


def main() -> int:
    robot_ip = os.environ.get("ROBOMASTER_IP")
    if not robot_ip:
        print("[stream_view] ROBOMASTER_IP is not set. Set it in .env "
              "(direct-connect AP mode is usually 192.168.2.1).", file=sys.stderr)
        return 2

    print(f"[stream_view] connecting to control port {robot_ip}:{CONTROL_PORT} ...",
          file=sys.stderr)
    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_sock.settimeout(3.0)
    try:
        control_sock.connect((robot_ip, CONTROL_PORT))
        send_and_expect(control_sock, "command")
        send_and_expect(control_sock, "stream on")
    except (OSError, RuntimeError) as exc:
        print(f"[stream_view] no robot at {robot_ip}:{CONTROL_PORT} ({exc}).\n"
              f"[stream_view] join the robot's Wi-Fi, or check ROBOMASTER_IP.",
              file=sys.stderr)
        control_sock.close()
        return 1
    print("[stream_view] stream enabled, connecting to video port ...", file=sys.stderr)

    video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_sock.settimeout(5.0)
    try:
        video_sock.connect((robot_ip, VIDEO_PORT))
    except OSError as exc:
        print(f"[stream_view] video port {robot_ip}:{VIDEO_PORT} unreachable ({exc}).",
              file=sys.stderr)
        try:
            send_and_expect(control_sock, "stream off")
        except Exception:
            pass
        video_sock.close()
        control_sock.close()
        return 1
    print("[stream_view] streaming H.264 to stdout ...", file=sys.stderr)

    cleaned_up = False

    def cleanup(*_args):
        nonlocal cleaned_up
        if cleaned_up:
            return
        cleaned_up = True
        print("\n[stream_view] shutting down, sending 'stream off;' ...", file=sys.stderr)
        try:
            send_and_expect(control_sock, "stream off")
        except Exception:
            pass  # best-effort, we're exiting regardless
        video_sock.close()
        control_sock.close()

    def handle_signal(*_args):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    out = sys.stdout.buffer
    try:
        while True:
            data = video_sock.recv(RECV_CHUNK)
            if not data:
                print("[stream_view] video socket closed by robot.", file=sys.stderr)
                break
            out.write(data)
            out.flush()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())