##### Pi is a fully fledged computer.
- Has a GPIO (General Purpose Input/Output) pins.
- Has a camera serial interface (CSI) and display serial interface (DSI), for touch display.
- Can use HaTs (Hardware Attached on Top) for additional functionality.
- ALSA (Advanced Linux Sound Architecture) for audio.
##### Arduino is a microcontroller
- [Blog](https://www.leorover.tech/post/raspberry-pi-or-arduino-when-to-choose-which)

##### purchased ardiuno starter kit [elegoo](https://www.amazon.com/dp/B01D8KOZF4?psc=1&smid=A2WWHQ25ENKVJ1&ref_=chk_typ_imgToDp)

240525
- set up arduino ide on windows 11, could not see the controller
- set up arduino ide on Raspian (couldn't make installer with kit work, used add /remove programs to pick up packages) and connected to pi
- completed blinking light project
- ![lab station](images/lab_station.png)

240526
- completed push button light project, with bread board, resistor, and push button.
- explored kit components.
- ![pi-arduino](images/pi-arduino.png)

240601
- installed Raspberry 5
- updated software, installed arduino and vscode IDEs

240607
- attending [South East Linux Fest](https://southeastlinuxfest.org/self-2014-2/)
- Exploring home automation tools,
  -  [Script Server](https://github.com/bugy/script-server)
  - [VimWiki](https://vimwiki.github.io/vimwikiwiki/)
- AI suggested: such as [Home Assistant](https://www.home-assistant.io/), [OpenHAB](https://www.openhab.org/), and [Node-RED](https://nodered.org/) 

240622
- bought [magnifying glass headset](https://www.amazon.com/dp/B07T4KPYN2?psc=1&ref=ppx_yo2ov_dt_b_product_details)
- realized I had the LED in backwards, which is why it wouldn't work with the switch, only the onboard led was lighting up.
- updated code to get a better "debounce" state.

240630
- Created fade in / fade out for a pulsing LED.
-![led](images/led.png)
- Explored positive / negative buses on breadboard. Not able to leverage them yet; using them instead of punching down right next to the resistor or LED lead didn't functino as expected.
- Combined LED and toggle as before. NOw fades in and out when pressed, otherwise off.
- ![led-button](images/led_button.png)