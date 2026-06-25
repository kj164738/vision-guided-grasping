from setuptools import find_packages, setup

package_name = "camera_source"

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
    description="Publishes ROS2 images from a USB camera or local video file.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "camera_source_node = camera_source.camera_source_node:main",
        ],
    },
)
