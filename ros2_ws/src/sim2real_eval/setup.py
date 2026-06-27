from setuptools import find_packages, setup

package_name = "sim2real_eval"

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
    description="Offline domain randomization trial generation and robustness reporting.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "generate_trials = sim2real_eval.generate_trials:main",
            "summarize_results = sim2real_eval.summarize_results:main",
        ],
    },
)
