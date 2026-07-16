#ifndef ROBOMASTER_DRIVER__HARDWARE_INTERFACE_HPP_
#define ROBOMASTER_DRIVER__HARDWARE_INTERFACE_HPP_

#include <array>
#include <memory>
#include <string>
#include <vector>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/clock.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"

#include "robomaster_driver/tcp_client.hpp"

namespace robomaster_driver {

// ros2_control SystemInterface for the physical DJI RoboMaster EP,
// talking to the plaintext SDK over TCP. Mirrors gz_ros2_control's
// role on the sim side: sim.launch.py loads the Gazebo plugin,
// tether.launch.py loads this one, against the same controller_manager
// config and the same four wheel joint names.
//
// Command interfaces (velocity, rad/s), one per wheel joint, names
// taken from <robot_param_prefix>ros2_control URDF block:
//   front_left_wheel_joint, front_right_wheel_joint,
//   rear_left_wheel_joint,  rear_right_wheel_joint
// matching wheel.urdf.xacro's ${name}_wheel_joint naming.
//
// State interfaces (velocity): NOT real encoder feedback. The
// plaintext SDK's chassis push only exposes position/attitude/status,
// not per-wheel rpm, and polling "chassis speed ?" on the same
// connection used for writes would block the control loop. State here
// echoes the last commanded velocity. Fine for open-loop motion;
// revisit if the attack demo needs closed-loop odometry.
class HardwareInterface : public hardware_interface::SystemInterface {
public:
  RCLCPP_SHARED_PTR_DEFINITIONS(HardwareInterface)

  hardware_interface::CallbackReturn
  on_init(const hardware_interface::HardwareInfo &info) override;

  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override;

  hardware_interface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State &previous_state) override;
  hardware_interface::CallbackReturn
  on_deactivate(const rclcpp_lifecycle::State &previous_state) override;

  hardware_interface::return_type read(const rclcpp::Time &time,
                                       const rclcpp::Duration &period) override;
  hardware_interface::return_type
  write(const rclcpp::Time &time, const rclcpp::Duration &period) override;

private:
  static constexpr size_t kNumWheels = 4;
  // Order matches the plaintext SDK's w1..w4 mapping:
  // w1 = front-right, w2 = front-left, w3 = rear-right, w4 = rear-left.
  // See protocol_api.html#chassis-wheel-speed-control.
  enum WheelIndex {
    kFrontRight = 0,
    kFrontLeft = 1,
    kRearRight = 2,
    kRearLeft = 3
  };

  std::array<double, kNumWheels>
      wheel_velocity_command_{}; // rad/s, from controller
  std::array<double, kNumWheels> wheel_velocity_state_{}; // rad/s, echoed back

  // Set from <param name="wheel_radius_m">...</param> in the URDF
  // ros2_control block; needed to convert rad/s -> the SDK's rpm.
  double wheel_radius_m_ =
      0.05; // matches wheel collision radius in wheel.urdf.xacro
  std::string robot_ip_ = std::getenv(
      "ROBOMASTER_IP"); // direct-connection default, see connection.html
  int control_port_ = 40923;

  std::unique_ptr<TcpClient> tcp_client_;
  rclcpp::Clock steady_clock_{
      RCL_STEADY_TIME}; // for RCLCPP_*_THROTTLE, must be a stable member
};

} // namespace robomaster_driver

#endif // ROBOMASTER_DRIVER__HARDWARE_INTERFACE_HPP_