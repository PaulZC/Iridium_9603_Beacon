# Iridium 9603N Beacon Assembly Instructions

Here are the assembly instructions for V5 of the Iridium 9603N Beacon:

### Blank PCB

Start by having the blank PCBs manufactured. If you are based in the UK or Europe, I can recommend
[Multi-CB](https://www.multi-circuit-boards.eu/en/index.html) who can manufacture PCBs in 1-8 working days and
can process the Eagle .brd file direct - there's no need to generate Gerber files.

My recommended options are:
- Layers: 2 layers
- Format: single pieces
- Surface finish: chemical gold (ENIG)
- Material: FR4, 1.55mm
- Cu layers: 35um
- Solder stop: both sides, green
- Marking print: both sides, white

![V5_Assembly_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_1.JPG)

### Add solder paste

Multi-CB can also provide you with a solder paste (SMD) stencil for the PCB. My recommended options are:
- SMD stencil for: top layer
- Make the Y dimension 20mm longer than the PCB itself to allow you to fix it down with tape
- Type: custom
- Pad reduction: yes, 10%
- Thickness: 100um
- Existing fiducials: lasered through
- Text type: half lasered
- Double-sided brushing: yes

The solder paste stencil will - by default - have tCream cut-outs for _all_ of the surface mount components.
If you intend to solder some of the components by hand, you can if you wish provide a separate stencil design
containing cut-outs for only the 'tricky' components: J1 and U3 in particular.

I secure the blank PCB onto a flat work surface by locating it between two engineer's squares. I use a sheet of toughened glass
as the work surface as it is both very flat and easy to clean.

![V5_Assembly_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_2.JPG)

Use the two round fiducials to line up the stencil with the PCB. Secure the stencil with tape.

![V5_Assembly_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_3.JPG)

Apply solder paste close to the component cut-outs and then scrape the paste over the stencil using a knife blade
or a similar straight edge. Take appropriate safety precautions when working with solder paste - particularly if you are using
tin-lead solder instead of lead-free.

![V5_Assembly_4](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_4.JPG)

![V5_Assembly_5](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_5.JPG)

![V5_Assembly_6](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_6.JPG)

### Position the surface mount components

Position the components onto the blobs of solder paste using tweezers. A magnifier lamp or a USB microscope will
help you place the components in the correct position. J1 - the 20-way Samtec connector - is probably the trickiest
component to position. Take extra time to make sure the legs are centered accurately on the pads.

![V5_Assembly_7](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_7.JPG)

### Reflow the surface mount components

Use a reflow oven to heat the circuit board to the correct temperatures to melt the solder. A reflow oven doesn't need to be
expensive. The one shown below was assembled from:

- Quest 9L 1000W mini-oven
- Inkbird PID temperature controller and 40A solid state relay
- Type K thermocouple

Several people have published good reflow oven construction guides, including [this one](http://www.die4laser.com/toaster/index.html).

![V5_Assembly_8](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_8.JPG)

Use the correct temperature profile for your solder paste, but you won't go far wrong with 160C for four minutes, followed by
210C for one minute, followed by a cool-down with the door open. Use a flashlight to check that the solder has melted across
the whole PCB at 210C. Hold the temperature at 210C a little longer if some of the solder paste still appears 'gray' instead of 'silver'.

![V5_Assembly_9](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_9.JPG)

### Check for shorts

Carefully examine all the solder joints and correct any shorts you find.

The 'trick' to removing a short is to add more solder or solder paste and then to use
copper solder braid or wick to remove all the solder in one go.

![Shorts_1](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Shorts_1.JPG)

![Shorts_2](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Shorts_2.JPG)

![Shorts_3](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/Shorts_3.JPG)

Solder any remaining surface mount components by hand and then use a cotton bud (q-tip) dipped in Iso-Propyl Alcohol
(IPA / Propanol / rubbing alcohol) to remove any flux residue.

All being well, your PCB should look like this:

![V5_Assembly_10](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_10.JPG)

### Press-in nuts

The Iridium 9603N module is held in place by two 2-56 screws. The threaded 2-56 press-in nuts now need to be pressed into the rear of the
PCB. These are McMaster part number 95117A411. The nuts are best pressed into place using an arbor press, but the corners of the circuit
board have been deliberately kept clear of components so you can press the nuts in using a standard workshop vice if required.

![V5_Assembly_11](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_11.JPG)

### Add the non-surface mount components

The non-surface mount components (battery clips, relay, super capacitors, SMA conectors) can now be soldered in by hand. If you are
going to be using solar power, omit the battery clips and use 10F super capacitors instead of 1F. See
[Power Options](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/LEARN.md#power-options) for further details.

![V5_Assembly_12](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_12.JPG)

![V5_Assembly_13](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_13.JPG)

### Install the bootloader

The SAMD21G18A processor now needs to be configured with a bootloader using a J-Link programmer or similar. See
[How do I install the ATSAMD21G18 Bootloader](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/LEARN.md#how-do-i-install-the-atsamd21g18-bootloader)
for further details.

![V5_Assembly_14](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_14.JPG)

### Test the PCB

Before connecting the Iridium 9603N, it is a good idea to test the completed PCB. The [Arduino](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino)
directory contains a sketch called Iridium_9603N_Beacon_V5_Test which will test all of the components on the PCB for you. Messages are displayed
on the Arduino IDE Serial Monitor as each test is passed.

### Install the Iridium 9603N module

Take appropriate ESD precautions throughout and especially when handling the 9603N module.

Connect the 9603N to the beacon PCB using a HIROSE (HRS) u.FL-u.FL cable or similar. The cable needs to be 50 Ohm and approximately 50mm long.

![V5_Assembly_15](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_15.JPG)

Carefully fold the 9603N module over onto the PCB, insert the 20-way connector into the Samtec socket, then secure the module using:
- two 4.5mm OD x 6mm spacers (McMaster 94669A100)
- two 2-56 x 7/16" screws (McMaster 92185A081)

![V5_Assembly_16](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_16.JPG)

![V5_Assembly_17](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_17.JPG)

Screw the GNSS and Iridium antennas onto the SMA connectors

![V5_Assembly_18](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_18.JPG)

### Retest the PCB

Now that the 9603N has been installed, retest the completed PCB using the [Arduino test code](https://github.com/PaulZC/Iridium_9603_Beacon/tree/master/Arduino).

### Lacquer the PCB

I do recommend giving the PCB a coat of lacquer, especially if you are intending to use it to track a balloon flight.
Cover all of the surface mount components with [Acrylic Protective Lacquer (conformal coating)](https://uk.rs-online.com/web/p/conformal-coatings/3217324/)
except: U4 (pressure sensor), J1, SW1, CON1, IO pads and split pads. You will need to temporarily remove the 9603N
while you apply the lacquer.

![V5_Lacquer.JPG](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Lacquer.JPG)

### Ready to fly!

Insert three Energiser® Ultimate Lithium AA batteries into the battery clips

![V5_Assembly_19](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_19.JPG)

The completed beacon is an almost perfect fit in a [Peli 1015 Micro Case](https://peliproducts.co.uk/1015-micro-case.html)
(The 1015 case is also available in Clear&Yellow or Clear&Black)

![V5_Assembly_20](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_20.JPG)

![V5_Assembly_21](https://github.com/PaulZC/Iridium_9603_Beacon/blob/master/img/V5_Assembly_21.JPG)

### The Small Print

This project is distributed under a Creative Commons Attribution + Share-alike (BY-SA) licence.
Please refer to section 5 of the licence for the “Disclaimer of Warranties and Limitation of Liability”.

Enjoy!

**_Paul_**