Measurement Points
==================


General
-------------
A wassermonitor measurement point consists of a raspberry pi (raspi), a stack of adapter cards to
talk with sps-standard-sensors and the sensors with their setup themselves.

The raspi is responsible for the following features:
    * General
        * Read structure and sensor information from a configuration file
        * Talk with sensors and save measurement values in a local sqlite-file
        * Convert raw-value to calibrated value
        * Sign the stored measurement data with private key and send them to the server api
    * Additional
        * Provide script for calibration file generation


Example
-------
In this example we see the following setup.


.. figure:: pictures/Measurement_Principle.svg
    :width: 80%

    Typical measurement point setup with a single raspberry pi connected with two sensors via an sps-adapter-card-stack.
    With the current setup, four sensors can be connected to a single raspi.

.. image:: pictures/Meas_Setup_details.svg

.. toctree::
   :maxdepth: 3
   :caption: Contents: