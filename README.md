# Wassermonitor2

New Implementation of Wassermonitor

Wassermonitor is a full implementation for collecting data from distributed sensors and monitoring the data. Goal of the project ist to present the catpured data on a dashboard and warn via email, telegram or signal, if defined borders are crossed.

The Project is currently under development, but I'm sure to deploy a full implementation in a few weeks.

## Current Status

### Features 
| Module    | Feature                                 | Status                |
|-----------|-----------------------------------------|-----------------------|
| API       | Get new signed Measurement values       | 🟢 Completed          |
|           | Provide current values                  | 🟢 Completed          |
|           | Provide values over time with deviation | 🟢 Completed          |
| Dashboard | Show current status plot                | 🟢 Completed          |
|| Show time plot | 🟢 Completed          |
|| Show devation plot | 🟢 Completed          |
|| Support light and dark mode | 🟢 Completed          |
| Warning Bot | Warn via telegram | 🟢 Completed          |
|| Warn via email | 🟡 In Progress        |
|| Warn via signal | 🟡 In Progress        |
|| Support multi language | 🟢 Completed (en, de) |
| Datacrawler | Crawl data from I2C sensors | 🟢 Completed          |
| Datatransmitter | Sign data with psk and send to API | 🟢 Completed          |

### Documentation
| Module     | Documentation feature | Status |
|------------|---|---|
| API        | Doc-Strings for Sphinx | 	🟢 Completed|
|            | Full Text Documentation | 	🔴 Not Started |
| warningbot | Doc Strings for Sphinx |   🟡 In Progress |
|            | Full Text documentation |  	🔴 Not Started |
| Pi         | Doc-Strings for Sphinx | 	🟢 Completed|
|            | Full Text documentation |  🟡 In Progress |
|Setup Guide | full Text documentation | 	🟡 In Progress |


### Deployment
| Feature                                                                         | Status |
|---------------------------------------------------------------------------------|---|
| If push to main-branch: Github Action: Automatically deploy documentation       | 🟢 Completed  | 
| If push to main-branch: Github Action: Automatically build .tar.gz packets                              | 	🔴 Not Started |
| If push to main-branch: Github Action: Automatically build docker containers for server and meas_points | 	🔴 Not Started |

## Full documentation

Please find the full documentation under https://doc.wassermonitor.de. 


## Setup


### Server

The server runs an API to receive data from the measurement points. It offers a dashboard in which the current measured value of each connected sensor is displayed, sorted by measuring point, as well as the time course of the measured values and their derivation. 
In addition, the server provides a warning bot that can send warnings by e-mail, telegram or pulse signal if warning and alarm limits are exceeded.
 

### Raspberry Pi

Each measurement point is consist of the sensors and a raspberry pi which collects the data of the sensors. The data then is temporarily stored until it can be sent to the API of the server. The raspi needs some upgrades to talk with sps sensors via i2c. Please see the full documentation to
read more about the full setup of a measurement point including hard- and software.

## Recommendation

If you want to use the water monitor for a public presentation on the Internet, please ensure that the data is sufficiently anonymised. If, for example, the water monitor is used to monitor a fire-fighting water reservoir, it is probably quite safe to make the data publicly accessible.
When it comes to water supply, it can be very questionable to make the data publicly accessible on the internet. For example, if only one household is supplied, the data can provide real-time information about whether someone is at home or not. It is less questionable if the monitored system supplies many households, as a certain degree of anonymisation is then achieved. 
You should therefore consider very carefully whether the data is sufficiently anonymised before making it publicly accessible. Otherwise, it may be advisable to only make the data visible within a VPN.





