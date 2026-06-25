from setuptools import find_packages, setup

package_name = "yolo_world_ros"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="vision-guided-grasping",
    maintainer_email="user@example.com",
    description="ROS2 wrapper for YOLO-World open-vocabulary detection.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "yolo_world_node = yolo_world_ros.yolo_world_node:main",
        ],
    },
)
