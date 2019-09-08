# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 22:18:21 2019

@author: Guest Group
"""
from biosteam.biorefineries.lipidcane.system.ethanol import ethanol_sys, Sugar_solution
from biosteam.biorefineries.lipidcane.system.biodiesel import biodiesel_sys, Oil
from biosteam.biorefineries.lipidcane.system.pretreatment import \
    pretreatment_sys, pretreatment_species, F4, Lipid, Sugar
from biosteam.biorefineries.lipidcane.tea import LipidcaneTEA
from biosteam.units.facilities import CoolingTower, \
                                      BoilerTurbogenerator, \
                                      ChilledWaterPackage, \
                                      ProcessWaterCenter
from biosteam import System, Stream, find, Species
from biosteam.units import Junction, InvSplitter
from biosteam.biorefineries.lipidcane.utils import set_lipid_fraction
import warnings

warnings.filterwarnings('ignore')

__all__ = ('lipidcane_sys', 'lipidcane_tea')

# %% Facilities
Stream.species = pretreatment_species
emission = Stream('Emission')
water = Species('Water',)
stream = find.stream

BT = BoilerTurbogenerator('BT',
                          ins=F4-0,
                          outs=emission,
                          boiler_efficiency=0.80,
                          turbogenerator_efficiency=0.85)

Stream.species = water
CT = CoolingTower('CT')
process_water_streams = (stream.Water_1, stream.Water_2,
                         stream.Imbibition_water,
                         stream.S134, stream.Water_3)
recycle_water_streams = (stream.Water_4,)
makeup_water = Stream('Makeup water', price=0.000254)
BT_makeup_water = Stream('BT makeup water', price=0.000254)
CT_makeup_water = Stream('CT makeup water', price=0.000254)
process_water = Stream('Process water')
recycle_water = Stream('Recycle water')

def update_water():
    process_water._mol[0] = sum([i.getflow('Water') for i in process_water_streams])
    recycle_water._mol[0] = sum([i.getflow('Water') for i in recycle_water_streams])

CWP = ChilledWaterPackage('CWP')
PWC = ProcessWaterCenter('PWC',
                         ins=(recycle_water, makeup_water, BT_makeup_water, CT_makeup_water),
                         outs=(process_water, 'BT_water', 'CT_water'),
                         BT=BT, CT=CT)

# %% Set up system
connect_sugar = Junction(Sugar, Sugar_solution, ('Water', 'Glucose', 'Sucrose'))
connect_lipid = Junction(Lipid, Oil, ('Lipid',))

lipidcane_sys = System('lipid cane system',
                       network=pretreatment_sys.network
                             + (connect_sugar, connect_lipid)
                             + ethanol_sys.network
                             + biodiesel_sys.network,
                       facilities=(CWP, BT, CT, update_water, PWC))
units = lipidcane_sys._costunits

# %% Perform TEA
lipidcane_sys.reset_names()
lipidcane_tea = LipidcaneTEA(system=lipidcane_sys, IRR=0.15, duration=(2018, 2038),
                             depreciation='MACRS7', income_tax=0.35,
                             operating_days=200, lang_factor=3,
                             construction_schedule=(0.4, 0.6), WC_over_FCI=0.05,
                             labor_cost=2.5e6, fringe_benefits=0.4,
                             property_tax=0.001, property_insurance=0.005,
                             supplies=0.20, maintenance=0.01, administration=0.005)
set_lipid_fraction(0.10)
lipidcane_sys.simulate()
lipidcane_tea.solve_IRR()