# Team Baby Musks WRO Bot
The bot's working procedure involves mobility management, power and sense management, and the coordination of its key components, including motors, sensors, and processors.Here is a basic overview of how everything has to be done.


Careful selection and integration of motors into the vehicle's chassis.
Precise mounting of all necessary components.
Consideration of basic engineering principles like speed, torque, and power utilization.
Assembly instructions and availability of 3D CAD files for component printing.
Coordination of front and back motors for vehicle movement.
Front wheels controlled by a servo motor, while back wheels use a gear motor.
Precise control of servo angles for smooth vehicle rotation.
Manoeuvrability enhanced by smaller wheels with thin widths.
Mounting of components on a chassis structure, including motors and sensors.

Using an 1800mAh LiPo battery as the power source.
Utilization of step-up and step-down buck converters to adjust voltage for different components.
Sensors, including HC-SR04 Ultrasonic Distance Sensor, Raspberry Pi Camera Module 3, and a 10-DOF IMU Sensor for motion tracking.
The IMU Sensor combines accelerometers, gyroscopes, and magnetometers for accurate motion tracking.
Jetson Nano processor for capturing and processing visual data, making real-time navigation decisions, and controlling actuators.
Arduino Uno for interfacing with sensors and controlling physical components like motors and servos.
Communication between Jetson Nano and Arduino Uno for real-time control and adaptation to changing conditions.
The bot's working mechanism involves:

Capturing and processing visual data from the Pi Camera using the Jetson Nano.
Making real-time navigation decisions based on image analysis to avoid obstacles and follow paths.
Sending control commands to the Arduino Uno for motor and actuator control.
Continuously looping through this process to enable autonomous navigation and adaptation to the environment.
Precise control of motor speeds and directions for various movements.
In summary, the bot's key components and their coordination allow it to operate autonomously by processing visual data, making navigation decisions, and controlling physical components for mobility, all while adapting to its surroundings in real-time.
