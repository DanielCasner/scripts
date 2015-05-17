#!/usr/bin/env python2
"""
Tree drip irrigation calculator based on information at
http://forestry.usu.edu/htm/city-and-town/tree-care/drip-irrigation
"""
__author__ = "Daniel Casner <www.danielcasner.org>"

conversionFactor = 0.623 # This conversion factor is simply the gallons of water applied when you irrigate one square foot of ground with one inch of water.

crownDiameter = input("Tree crown diameter (ft)>>> ")

plantArea = crownDiameter * crownDiameter * 0.7854 # Plant Area = Diameter of drip-line or crown diameter squared x 0.7854

plantFactor = input("""This is factor that helps correct for the fact that not all plants use water at the same rate under the same conditions. The following are examples of some research-derived plant factors.
* 1.00 Ground covers, flower beds, evergreens, some perennials, small shrubs (under 4' tall), vines
* 0.85 Apples, cherries, walnuts
* 0.80 Mature shade trees (broadleaved trees)
* 0.75 Pecans, peaches, plums, pears, apricots, almonds
* 0.70 Native plants in semi-arid areas, some ornamental plants, large shrubs (over 4' tall)
* 0.40 Established low-water use native or other low water-use plants
>>> """)

pet = input("Potential Evapotranspiration / day (typically 0.35-0.40) >>> ")

dripSystemEfficency = input("Drip system efficency (typically 0.85-0.90) >>> ")

gallons = conversionFactor * plantArea * plantFactor * pet / dripSystemEfficency

# Soil texture determines how much area is wetted by each emitter:
# Sandy texture 5 to 21 square feet
# Loam texture 21 to 65 square feet
# Clay texture 65 to 161 square feet
emitterWetting = 65 # ft sq

emittersNeeded = plantArea / emitterWetting

print gallons, "gallons per day required"
print emittersNeeded, "emitters will be needed"
