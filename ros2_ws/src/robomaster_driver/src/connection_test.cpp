// Minimal standalone connectivity check. Not a ROS2 node - deliberately
// has no rclcpp::Node, no controller_manager, no URDF dependency. Run
// this FIRST before wiring up the full ros2_control stack: it tells
// you in about two seconds whether the robot is reachable at all,
// which collapses a lot of otherwise-ambiguous failure modes (wrong
// Wi-Fi network, robot not in direct-connection mode, robot not
// powered on, wrong IP) down to one clear pass/fail.
//
// Usage:
//   ros2 run robomaster_driver connection_test [robot_ip]
//   (defaults to the IP set in .env)
//
// What it does, in order:
//   1. TCP connect to <ip>:40923
//   2. send "command;", expect "ok;"          -> confirms SDK mode
//   3. query "robot battery ?;"                -> confirms two-way traffic
//   4. send a zero-velocity chassis command     -> confirms write path,
//      without actually moving the robot
//   5. cleanly send "quit;" and disconnect
#include <iostream>
#include <string>

#include "robomaster_driver/tcp_client.hpp"

int main(int  /*argc*/, char ** /*argv*/) {
  std::string robot_ip = std::getenv("ROBOMASTER_IP");

  std::cout << "RoboMaster EP connection test\n";
  std::cout << "  target: " << robot_ip << ":40923\n";
  std::cout
      << "  make sure you're joined to the robot's Wi-Fi hotspot and it's\n";
  std::cout << "  in direct-connection mode (switch on the smart central "
               "control)\n\n";

  robomaster_driver::TcpClient client;

  std::cout << "[1/4] connecting + entering SDK mode... ";
  if (!client.connect(robot_ip)) {
    std::cout << "FAILED\n";
    std::cout << "\nCouldn't connect. Check: robot powered on, "
                 "direct-connection mode,\n";
    std::cout << "PC joined to the robot's Wi-Fi hotspot, IP is " << robot_ip << ".\n";
    return 1;
  }
  std::cout << "ok\n";

  std::cout << "[2/4] querying battery level... ";
  std::string response;
  if (!client.send_command("robot battery ?", response)) {
    std::cout << "FAILED (no response)\n";
    return 1;
  }
  std::cout << response << "%\n";

  std::cout << "[3/4] setting movement mode to free... ";
  if (!client.send_command("robot mode free", response) || response != "ok") {
    std::cout << "FAILED (got '" << response << "')\n";
    return 1;
  }
  std::cout << "ok\n";

  std::cout << "[4/4] sending zero-velocity chassis command (write-path check, "
               "robot should NOT move)... ";
  if (!client.send_command("chassis wheel w1 0 w2 0 w3 0 w4 0", response) ||
      response != "ok") {
    std::cout << "FAILED (got '" << response << "')\n";
    return 1;
  }
  std::cout << "ok\n";

  client.disconnect();
  std::cout << "\nAll checks passed. Robot is reachable and accepting SDK "
               "commands.\n";
  return 0;
}