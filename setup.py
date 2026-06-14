from setuptools import find_packages, setup


setup(
    name="pangolin-eval",
    version="0.2.1",
    description="Measure LLM workloads across cost, latency, quality, and reliability.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    entry_points={"console_scripts": ["pangolin-eval=pangolin_eval.cli:main"]},
)
