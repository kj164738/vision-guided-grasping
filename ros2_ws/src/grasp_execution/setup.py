from setuptools import find_packages, setup

package_name = "grasp_execution"

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
    description="Lightweight grasp execution state machine for Isaac Sim demos.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "simple_grasp_executor_node = grasp_execution.simple_grasp_executor_node:main",
        ],
    },
)
