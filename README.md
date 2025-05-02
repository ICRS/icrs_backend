# 🗃️ ICRS Back End

## [💻 MAIN CODEBASE: https://github.com/ICRS/icrs_lab](https://github.com/ICRS/icrs_lab)

## 👋 Introduction

This project contains the necessary infrastructure for interfacing with the numerous systems in the lab

## Projects:

* Server: contains all the necessary components for the lab
* Bambu Printer Gateway: a translation layer from bambu p1 printers to REST service
* Registration Page: React project for registering new users

## 🔨 Build and Deployment Instructions

### Docker Publishing
Each python subproject has definitions for building a docker image, these are distributed to dockerhub <https://hub.docker.com/u/icroboticssociety>.
To trigger a publishing of the docker update the `pyproject.toml` file (make sure that the workflow files are setup correctly).

### More info

See [https://github.com/ICRS/icrs_lab](https://github.com/ICRS/icrs_lab)

## 📝 Paper

https://www.researchgate.net/publication/385302645_Automated_Student_3D_Printing_Verification_Process


## 💬 Contact

For any questions please reach out to us at [icrobotics@imperial.ac.uk](mailto:icrobotics@imperial.ac.uk)
