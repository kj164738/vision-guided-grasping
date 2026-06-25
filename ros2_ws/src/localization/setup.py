from setuptools import find_packages, setup

package_name = "localization"

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
    description="RGB-D object localization and TF-based frame transformation.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "object_localizer_node = localization.object_localizer_node:main",
        ],
    },
)
