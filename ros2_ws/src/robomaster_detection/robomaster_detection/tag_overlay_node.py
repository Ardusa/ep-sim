#!/usr/bin/env python3
"""Draws apriltag_ros detections onto the camera image for eyeballing.

Purely a debug view — nothing control-related subscribes to it. Publishes
/camera/image_annotated; view with:

    ros2 run rqt_image_view rqt_image_view /camera/image_annotated

Images and detections arrive on separate topics with no delivery-order
guarantee, so they're paired with an ApproximateTimeSynchronizer rather than
by drawing the newest detection on the newest frame (which would smear boxes
onto the wrong frame while moving).
"""
import cv2
import rclpy
from apriltag_msgs.msg import AprilTagDetectionArray
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
from rclpy.node import Node
from sensor_msgs.msg import Image

_GREEN = (0, 255, 0)
_MAGENTA = (255, 0, 255)


class TagOverlayNode(Node):
    def __init__(self):
        super().__init__("tag_overlay_node")

        self.declare_parameter("queue_size", 10)
        # Max stamp difference to still call an image and a detection a pair.
        # Loose enough to survive detector latency at 30fps, tight enough not to
        # pair across frames.
        self.declare_parameter("slop", 0.1)

        self._bridge = CvBridge()
        self._pub = self.create_publisher(Image, "/camera/image_annotated", 10)

        queue_size = self.get_parameter("queue_size").value
        image_sub = Subscriber(self, Image, "/camera/image_raw")
        tags_sub = Subscriber(self, AprilTagDetectionArray, "/detections")
        self._sync = ApproximateTimeSynchronizer(
            [image_sub, tags_sub], queue_size, self.get_parameter("slop").value
        )
        self._sync.registerCallback(self._on_pair)

    def _on_pair(self, image_msg, tags_msg):
        frame = self._bridge.imgmsg_to_cv2(image_msg, "bgr8")

        for tag in tags_msg.detections:
            corners = [(int(c.x), int(c.y)) for c in tag.corners]
            for i, corner in enumerate(corners):
                cv2.line(frame, corner, corners[(i + 1) % len(corners)], _GREEN, 2)

            centre = (int(tag.centre.x), int(tag.centre.y))
            cv2.circle(frame, centre, 4, _MAGENTA, -1)
            cv2.putText(
                frame,
                f"id {tag.id}",
                (centre[0] + 8, centre[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                _MAGENTA,
                2,
            )

        annotated = self._bridge.cv2_to_imgmsg(frame, "bgr8")
        annotated.header = image_msg.header
        self._pub.publish(annotated)


def main(args=None):
    rclpy.init(args=args)
    node = TagOverlayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
