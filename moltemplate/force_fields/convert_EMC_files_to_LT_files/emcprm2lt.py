#!/usr/bin/env python

# Author: David Stelter, Andrew Jewett
# License: MIT License  (See LICENSE.md)
# Copyright (c) 2017
# All rights reserved.

import os, sys, getopt
import datetime

__version__ = '0.3.0'

#################### UNITS ####################
# Only used with --units flag
econv = 1.0 # Additional Factor for unit conversion if needed (energies)
lconv = 1.0 # Additional Factor for unit conversion if neededa (lengths)
dconv = 1.0 # Additional Factor for unit conversion if neededa (densities)
###############################################

sys.stderr.write('\nEMC 2 LT conversion tool: v'+str(__version__)+'\n\n')

def helpme():
    sys.stderr.write('Help for the EMC 2 LT conversion tool\n\n')
    sys.stderr.write('Input takes a list of files in EMC .prm format to be read.\n')
    sys.stderr.write('Additional styles (bond, angle, etc) can be modified via the\n'+
          'command line. Any valid LAMMPS style can be used.\n\n')
    sys.stderr.write('Styles include:\n')
    sys.stderr.write('--pair-style=\n')
    sys.stderr.write('--bond-style=\n')
    sys.stderr.write('--angle-style=\n')
    sys.stderr.write('--dihedral-style=\n')
    sys.stderr.write('--improper-style=\n\n')
    sys.stderr.write('Default styles are lj/cut/coul/long, harmonic, harmonic, harmonic,\n'+
                     'harmonic \n\n')
    sys.stderr.write('Other commands:\n')
    sys.stderr.write('--name= provides basename for output file if desired\n\n')
    sys.stderr.write('--units flag for manual units (no parameter needed)\n\n')
    sys.stderr.write('Usage example:\n')
    sys.stderr.write('emcprm2lt.py file1 file2 --bond-style=harmonic --angle-style=harmonic\n')
    sys.stderr.write('\n')

def Abort():
    sys.stderr.write('Aborting...\n')
    sys.exit()

def WriteInit():
# Write generic LAMMPS settings, likely need additional on a per-ff basis
    foutput.write('  write_once("In Init") {\n')
    foutput.write('    # Warning: This is a very generic "In Init" section, further\n')
    foutput.write('    # modification prior to any simulation is extremely likely\n')
    foutput.write('    units real\n')
    foutput.write('    atom_style full\n')
    foutput.write('    bond_style hybrid %s\n' % bstyle)
    if angle_flag:
        foutput.write('    angle_style hybrid %s\n' % astyle)
    if torsion_flag:
        foutput.write('    dihedral_style hybrid %s\n' % dstyle)
    if improp_flag:
        foutput.write('    improper_style hybrid %s\n' % istyle)
    foutput.write('    pair_style hybrid %s %f %f\n' % (pstyle,
            float(inner[0])*lconv, float(cutoff[0])*lconv))
    if pair14[0] == 'OFF':
        foutput.write('    special_bonds lj/coul 0.0 0.0 0.0\n')
    else:
        sys.stderr.write('Warning: special_bonds needed, add to "In Init" section\n\n')
    foutput.write('  } # end init\n')

def Units(length_flag, energy_flag, density_flag):
# Check flags for all units, determine what conversions are needed, hard-coded for LAMMPS 'real'
    sys.stderr.write('Attempting to auto-convert units... This should always be double-checked\n'+
                     ' especially for unique potential styles\n')
    global lconv; global econv; global dconv
    if length_flag:
        sys.stderr.write('Warning: Length scale does not match LAMMPS real units.\n'
                         '         Attempting conversion to angstroms.\n')
        if length[0] == 'NANOMETER':
            lconv = 10.0
            sys.stderr.write('  nanometer -> angstrom\n')
        elif length[0] == 'MICROMETER':
            lconv = 10000.0
            sys.stderr.write('  micrometer -> angstrom\n')
        elif length[0] == 'METER':
            lconv = 10000000000.0
            sys.stderr.write('  meter -> angstrom\n')
        else:
            sys.stderr.write('Length units NOT converted\n')
    if energy_flag:
        sys.stderr.write('Warning: Energy units do not match LAMMPS real units.\n'+
                         '         Attempting conversion to kcal/mol.\n')
        if energy[0] == 'KJ/MOL':
            econv = 0.239006
            sys.stderr.write('  kj/mol -> kcal/mol\n')
        elif energy[0] == 'J/MOL':
            econv = 0.000239006
            sys.stderr.write('  j/mol -> kcal/mol\n')
        elif energy[0] == 'CAL/MOL':
            econv = 0.001
            sys.stderr.write('  cal/mol -> kcal/mol\n')
        else:
            sys.stderr.write('Energy units NOT converted\n')
    if density_flag:
        sys.stderr.write('Warning: density units do not match LAMMPS real units.\n'+
                         '         Attempting conversion to gram/cm^3\n')
        if density[0] == 'KG/M^3':
            dconv = 0.001
            sys.stderr.write('  kg/m^3 -> g/cm^3\n')
        else:
            sys.stderr.write('Density units NOT converted\n')
    return lconv, econv, dconv

def ChkPotential(manual_flag, angle_flag, torsion_flag, improp_flag):
# Check type of potential, determine type of unit conversion is necessary
    global beconv
    if angle_flag:
        global aeconv
    if torsion_flag:
        global deconv
    if improp_flag:
        global ieconv
    if manual_flag == False:
        # Chk bond potential
        if bstyle == '' or bstyle == 'harmonic':
            beconv = econv / (2*pow(lconv,2))
        else:
            sys.stderr.write('Cannot find bond potential type, use manual units\n')
            Abort()
        if angle_flag:
            if astyle == '' or astyle == 'harmonic':
                aeconv = econv
            elif astyle == 'cosine/squared':
                aeconv = econv / 2
            elif astyle == 'sdk':
                aeconv = econv
            else:
                sys.stderr.write('Cannot find angle potential type, use manual units\n')
                Abort()
        # torsion and improper not implemented fully
        elif torsion_flag:
            if dstyle == '' or dstyle == 'harmonic':
                deconv = econv
            else:
                sys.stderr.write('Cannot find torsion potential type, use manual units\n')
                Abort()
        elif improp_flag:
            if istyle == '' or istyle == 'harmonic':
                ieconv = econv
            else:
                sys.stderr.write('Cannot find improper potential type, use manual units\n')
                Abort()
    else:
    # Modify as needed
        sys.stderr.write('Warning: Manual units used, set potential conversion units in script\n')
        beconv = 1
        if angle_flag:
            aeconv = 1
        if torsion_flag:
            deconv = 1
        if improp_flag:
            ieconv = 1


### Parse input ###
if len(sys.argv) == 1:
    helpme()
    sys.exit()
manual_units = False # Turned on via command line
args = list(sys.argv[1:])
myopts, args = getopt.gnu_getopt(args, 'fh', ['pair-style=', 'bond-style=', 'angle-style=',
    'dihedral-style=', 'improper-style=', 'name=', 'units'])
filenames = list(args)
pstyle = ''; bstyle = ''; astyle = ''; dstyle = ''; istyle = ''
name = ''
for opt, arg in myopts:
    if opt in ('-f'):
        filenames = arg
    elif opt in ('--pair-style'):
        pstyle = arg
    elif opt in ('--bond-style'):
        bstyle = arg
    elif opt in ('--angle-style'):
        astyle = arg
    elif opt in ('--dihedral-style'):
        dstyle = arg
    elif opt in ('--improper-style'):
        istyle = arg
    elif opt in ('--name'):
        name = arg
    elif opt in ('--units'):
        manual_units = True
        sys.stderr.write('Manual units enabled, modify python script accordingly')
    elif opt in ('-h', '--help'):
        helpme()
        sys.exit()

### Check input filenames, make sure they exist ###
sys.stderr.write('Converting: \n')
for i in range(len(filenames)):
    if os.path.isfile(filenames[i]):
        sys.stderr.write('\n'+filenames[i]+'\n')
    else:
        sys.stderr.write('invalid filename:'+filenames[i]+'\n')
        Abort()
sys.stderr.write('from EMC .prm to moltemplate .lt format\n\n')

### Open all files ###
f = [open(fname, 'r') for fname in filenames]

### All these settings from DEFINE should be list of fixed size ###
ffname = [[] for i in range(len(f))]
fftype = [[] for i in range(len(f))]
version = [[] for i in range(len(f))]
created1 = [[] for i in range(len(f))]
created2 = [[] for i in range(len(f))]
length = [[] for i in range(len(f))]
energy = [[] for i in range(len(f))]
density = [[] for i in range(len(f))]
mix = [[] for i in range(len(f))]
nbonded = [[] for i in range(len(f))]
inner = [[] for i in range(len(f))]
cutoff = [[] for i in range(len(f))]
pair14 = [[] for i in range(len(f))]
angle_def = [[] for i in range(len(f))]
torsion_def = [[] for i in range(len(f))]
improp_def = [[] for i in range(len(f))] # not all prm have this

### Parse DEFINE section, save info for each file ###
for i in range(len(f)):
    grab = False
    for line in f[i]:
        if line.strip() == 'ITEM	DEFINE':
            grab = True
        elif line.strip() == 'ITEM	END':
            grab = False
        elif grab:
            if line.startswith('FFNAME'):
                ffname[i] = line.split()[1].strip()
            if line.startswith('FFTYPE'):
                fftype[i] = line.split()[1].strip()
            if line.startswith('VERSION'):
                version[i] = line.split()[1].strip()
            if line.startswith('CREATED'):
                created1[i] = line.split()[1].strip()
                created2[i] = line.split()[2].strip()
            if line.startswith('LENGTH'):
                length[i] = line.split()[1].strip()
            if line.startswith('ENERGY'):
                energy[i] = line.split()[1].strip()
            if line.startswith('DENSITY'):
                density[i] = line.split()[1].strip()
            if line.startswith('MIX'):
                mix[i] = line.split()[1].strip()
            if line.startswith('NBONDED'):
                nbonded[i] = line.split()[1].strip()
            if line.startswith('INNER'):
                inner[i] = line.split()[1].strip()
            if line.startswith('CUTOFF'):
                cutoff[i] = line.split()[1].strip()
            if line.startswith('PAIR14'):
                pair14[i] = line.split()[1].strip()
            if line.startswith('ANGLE'):
                angle_def[i] = line.split()[1].strip()
            if line.startswith('TORSION'):
                torsion_def[i] = line.split()[1].strip()
            if line.startswith('IMPROP'):
                improp_def[i] = line.split()[1].strip()

### Sanity Checks ###
for i in range(len(f)):
    for j in range(len(f)):
        if ffname[j] != ffname[i]:
            sys.stderr.write('force field files do not match\n')
            Abort()
        if length[j] != length[i]:
            sys.stderr.write('units not identical between files\n')
            Abort()
        if energy[j] != energy[i]:
            sys.stderr.write('units not identical between files\n')
            Abort()
        if density[j] != density[i]:
            sys.stderr.write('units not identical between files\n')
            Abort()
        if inner[j] != inner[i]:
            sys.stderr.write('inner cutoff not identical between files\n')
            Abort()
        if cutoff[j] != cutoff[i]:
            sys.stderr.write('cutoff not identical between files\n')
            Abort()
        if pair14[j] != pair14[i]:
            sys.stderr.write('1-4 pair interaction not consistent between files\n')
            Abort()

### Check if sections exist in PRM file ###
angle_flag = False; torsion_flag = False; improp_flag = False
for i in range(len(f)):
    if angle_def[i] == 'WARN':
        angle_flag = True
    if torsion_def[i] == 'WARN':
        torsion_flag = True
    if improp_def[i] == 'WARN':
        improp_flag = True

### Check which units to use, trip convert flags ###
length_flag = False; energy_flag = False; density_flag = False
if length[0] != 'ANGSTROM':
    length_flag = True
if energy[0] != 'KCAL/MOL':
    energy_flag = True
if density[0] != 'G/CC':
    density_flag = True
if manual_units == True:
    length_flag = False
    energy_flag = False
    density_flag = False
Units(length_flag, energy_flag, density_flag)

### Read Whole File, save to lists ###
# Non-crucial sections include
# BONDS, ANGLE, TORSION, IMPROP, NONBOND
# Read all sections every time, only output sections when flags tripped
f = [open(fname, 'r') for fname in filenames]
masses = []; nonbond = []; bond = []; angle = []; torsion = []; improp = []
equiv = []
for i in range(len(f)):
    MASS = False
    NONBOND = False
    BOND = False
    ANGLE = False
    TORSION = False
    IMPROP = False
    EQUIV = False
    for line in f[i]:
        if line.strip() == 'ITEM	MASS':
            MASS = True
        elif line.strip() == 'ITEM	END':
            MASS = False
        elif MASS:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    masses.append(line.strip().split())
        if line.strip() == 'ITEM	NONBOND':
            NONBOND = True
        elif line.strip() == 'ITEM	END':
            NONBOND = False
        elif NONBOND:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    nonbond.append(line.strip().split())
        if line.strip() == 'ITEM	BOND':
            BOND = True
        elif line.strip() == 'ITEM	END':
            BOND = False
        elif BOND:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    bond.append(line.strip().split())
        if line.strip() == 'ITEM	ANGLE':
            ANGLE = True
        elif line.strip() == 'ITEM	END':
            ANGLE = False
        elif ANGLE:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    angle.append(line.strip().split())
        if line.strip() == 'ITEM	TORSION':
            TORSION = True
        elif line.strip() == 'ITEM	END':
            TORSION = False
        elif TORSION:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    torsion.append(line.strip().split())
        if line.strip() == 'ITEM	IMPROP':
            IMPROP = True
        elif line.strip() == 'ITEM	END':
            IMPROP = False
        elif IMPROP:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    improp.append(line.strip().split())
        if line.strip() == 'ITEM	EQUIVALENCE':
            EQUIV = True
        elif line.strip() == 'ITEM	END':
            EQUIV = False
        elif EQUIV:
            if not line.startswith('#'):
                if not line.startswith('\n'):
                    equiv.append(line.strip().split())
### Close prm files ###
for fname in f:
    fname.close()

### Sanity checks before writing LT files ###
# Check Equiv
for i in range(len(equiv)):
    for j in range(len(equiv)):
        if (equiv[i][0] == equiv[j][0]) and (equiv[i] != equiv[j]):
            sys.stderr.write('Error: Identical atom types with different equivalences\n')
            Abort()
# Check Masses
for i in range(len(masses)):
    for j in range(len(masses)):
        if (masses[i][0] == masses[j][0]) and (masses[i][1] != masses[j][1]):
            sys.stderr.write('Error: Identical types with different mass\n')
            Abort()
# Check Nonbond
for i in range(len(nonbond)):
    for j in range(len(nonbond)):
        if (nonbond[i][0] == nonbond[j][0]) and (nonbond[i][1] == nonbond[j][1]) and ((nonbond[i][2] != nonbond[j][2]) or (nonbond[i][3] != nonbond[j][3])):
            sys.stderr.write(str(nonbond[i])+'\n'+str(nonbond[j])+'\n')
            sys.stderr.write('Error: Identical types with different pair-interactions\n')
            Abort()

### Remove double equivalences ###
for i in range(len(equiv)):
    once = True
    for j in range(len(equiv)):
        if (equiv[i][0] == equiv[j][0]) and once:
            once = False
        elif (equiv[i][0] == equiv[j][0]):
            equiv[j][1] = None
            equiv[j][2] = 'duplicate'
    if len(equiv[i]) < 6:
        sys.stderr.write(str(equiv[i])+'\n')
        sys.stderr.write('Warning: Incorrect equivalence formatting for type '+
                         str(equiv[i][0])+'\n'+
                         '         Skipping type. Topology may not be complete.\n\n')
        equiv[i][1] = None
        equiv[i][2] = 'invalid_format'

### Check Potential Styles and Set Units ###
ChkPotential(manual_units, angle_flag, torsion_flag, improp_flag)

### Set output LT file ###
fname = 'ff_output.lt'
if name == '':
    fname = ffname[0] + '.lt'
else:
    fname = name + '.lt'
foutput = open(fname, 'w')

### Output to LT format ###
foutput.write('# Autogenerated by EMC 2 LT tool v'+
              __version__+' on '+
              str(datetime.date.today())+'\n')
foutput.write('#\n# ')
for i in range(len(sys.argv)):
    foutput.write('%s ' % sys.argv[i])
foutput.write('\n')
foutput.write('#\n')
foutput.write('# Adapted from EMC by Pieter J. in \'t Veld\n')
foutput.write('# Originally written as, FFNAME:%s STYLE:%s VERSION:%s on %s %s\n' %
        (ffname[0], fftype[0], version[0], created1[0], created2[0]))
foutput.write('\n')
foutput.write('%s {\n' % ffname[0])

# Charges not necessary? emc file assign charges in smiles, which would
# be in the per-molecule files created by moltemplate user... not here

### Mass Info ###
foutput.write('  write_once("Data Masses") {\n')
for i in range(len(masses)):
    if equiv[i][1] != None:
        foutput.write('    @atom:%s %f # %s\n' %
                (masses[i][0], float(masses[i][1]), masses[i][0]))
foutput.write('  } # end of atom masses\n\n')

### Equiv Info ###
# Write Equivalence
foutput.write('  # ----- EQUIVALENCE CATEGORIES for bonded interaction lookup -----\n')
for i in range(len(equiv)):
    if equiv[i][1] != None:
        foutput.write('  replace{ @atom:%s @atom:%s_b%s_a%s_d%s_i%s}\n' %
                (equiv[i][0], equiv[i][0], equiv[i][2], equiv[i][3], equiv[i][4], equiv[i][5]))
foutput.write('  # END EQUIVALENCE\n\n')
# Sanity check equivalences vs masses
for i in range(len(equiv)):
    check = None
    for j in range(len(masses)):
        if equiv[i][0] == masses[j][0]:
            check = 'success'
    if check == None:
        sys.stderr.write(str(equiv[i])+'\n'+str(masses[j])+'\n')
        sys.stderr.write('Atom defined in Equivlances, but not found in Masses\n')
        Abort()
# Sanity check masses vs equivalences
for i in range(len(masses)):
    check = None
    for j in range(len(masses)):
        if masses[i][0] == equiv[j][0]:
            check = 'success'
    if check == None:
        sys.stderr.write(str(masses[i])+'\n'+str(equiv[j])+'\n')
        sys.stderr.write('Atom defined in Masses, but not found in Equivlances\n')
        Abort()

### Nonbonded Info ###
if pstyle == '':
    sys.stderr.write('Warning: no non-bonded potential provided, assuming lj/cut/coul/long\n')
    pstyle = 'lj/cut/coul/long'
foutput.write('  write_once("In Settings") {\n')
foutput.write('    # ----- Non-Bonded interactions -----\n')
# Add new types from equivalence
for i in range(len(equiv)):
    once = True
    for j in range(len(nonbond)):
        # Get terms for new types
        if (equiv[i][0] != equiv[i][1]) and (equiv[i][1] == nonbond[j][0]):
            if not equiv[i][1] == nonbond[j][1]:
                line = '%s %s %s %s' % (equiv[i][0], nonbond[j][1], nonbond[j][2], nonbond[j][3])
                nonbond.append(line.split())
            if once:
                once = False
                line = '%s %s %s %s' % (equiv[i][0], equiv[i][0], nonbond[j][2], nonbond[j][3])
                nonbond.append(line.split())
        if (equiv[i][0] != equiv[i][1]) and (equiv[i][1] == nonbond[j][1]):
            line = '%s %s %s %s' % (equiv[i][0], nonbond[j][0], nonbond[j][2], nonbond[j][3])
            if line.split() != nonbond[-1]:
                nonbond.append(line.split())
for i in range(len(nonbond)):
    atom1name = None
    atom2name = None
    stylename = pstyle
    if pstyle == 'lj/sdk' or pstyle == 'lj/sdk/coul/long':
        stylename = 'lj%s_%s' % (nonbond[i][4], nonbond[i][5])
    # Cross Terms + Diagonal, normal
    for j in range(len(equiv)):
        if nonbond[i][0] == equiv[j][0]:
            atom1name = '%s_b%s_a%s_d%s_i%s' % (nonbond[i][0], equiv[j][2], equiv[j][3], equiv[j][4], equiv[j][5])
        if nonbond[i][1] == equiv[j][0]:
            atom2name = '%s_b%s_a%s_d%s_i%s' % (nonbond[i][1], equiv[j][2], equiv[j][3], equiv[j][4], equiv[j][5])
    if atom1name == None or atom2name == None:
        sys.stderr.write(str(atom1name)+'\n'+
                         str(atom2name)+'\n'+
                         str(nonbond[i])+'\n')
        sys.stderr.write('Error: Atom in Nonbonded Pairs not found in Equivalences\n')
        Abort()
    foutput.write('    pair_coeff @atom:%s @atom:%s %s %f %f' %
            (atom1name, atom2name, stylename, float(nonbond[i][3])*econv, float(nonbond[i][2])*lconv))
    foutput.write(' # %s-%s\n' % (nonbond[i][0], nonbond[i][1]))
foutput.write('  } # end of nonbonded parameters\n\n')

### Bond Info ###
if bstyle == '':
    sys.stderr.write('Warning: no bond potential provided, assuming harmonic\n')
    bstyle == 'harmonic'
foutput.write('  write_once("In Settings") {\n')
foutput.write('    # ----- Bonds -----\n')
for i in range(len(bond)):
    foutput.write('    bond_coeff @bond:%s-%s %s %f %f' %
            (bond[i][0], bond[i][1], bstyle, float(bond[i][2])*beconv, float(bond[i][3])*lconv))
    foutput.write(' # %s-%s\n' % (bond[i][0], bond[i][1]))
foutput.write('  }\n\n')
foutput.write('  write_once("Data Bonds By Type") {\n')
for i in range(len(bond)):
    foutput.write('    @bond:%s-%s @atom:*_b%s_a*_d*_i* @atom:*_b%s_a*_d*_i*\n' %
            (bond[i][0], bond[i][1], bond[i][0], bond[i][1]))
foutput.write('  } # end of bonds\n\n')

### Angle Info ###
if angle_flag:
    if astyle == '':
        sys.stderr.write('Warning: no angle potential provided, assuming harmonic\n')
        astyle == 'harmonic'
    foutput.write('  write_once("In Settings") {\n')
    foutput.write('    # ----- Angles -----\n')
    for i in range(len(angle)):
        if (len(angle[i]) > 5): # Check if extra data in angle array
            foutput.write('    angle_coeff @angle:%s-%s-%s %s %f %f' %
                    (angle[i][0], angle[i][1], angle[i][2], str(angle[i][5]), float(angle[i][3])*aeconv, float(angle[i][4])))
            foutput.write(' # %s-%s-%s\n' % (angle[i][0], angle[i][1], angle[i][2]))
        else:
            foutput.write('    angle_coeff @angle:%s-%s-%s %s %f %f' %
                    (angle[i][0], angle[i][1], angle[i][2], astyle, float(angle[i][3])*aeconv, float(angle[i][4])))
            foutput.write(' # %s-%s-%s\n' % (angle[i][0], angle[i][1], angle[i][2]))
    foutput.write('  }\n\n')
    foutput.write('  write_once("Data Angles By Type") {\n')
    for i in range(len(angle)):
        foutput.write('    @angle:%s-%s-%s @atom:*_b*_a%s_d*_i* @atom:*_b*_a%s_d*_i* @atom:*_b*_a%s_d*_i*\n' %
                (angle[i][0], angle[i][1], angle[i][2], angle[i][0], angle[i][1], angle[i][2]))
    foutput.write('  } # end of angles\n\n')

### Torsion/Dihedral Info ###a
# Incomplete
if torsion_flag:
    if dstyle == '':
        sys.stderr.write('Warning: no dihedral/torsion potential provided, assuming harmonic\n')
        dstyle == 'harmonic'
    foutput.write('  write_once("In Settings") {\n')
    foutput.write('    # ----- Dihedrals -----\n')
    for i in range(len(torsion)):
        foutput.write('    dihedral_coeff @dihedral:%s-%s-%s-%s %s %f %f %f %f\n' %
                (torsion[i][0], torsion[i][1], torsion[i][2], torsion[i][3], dstyle, float(torsion[i][4])*deconv, float(torsion[i][5]), float(torsion[i][6])))
    foutput.write('  }\n\n')
    foutput.write('  write_once("Data Dihedrals By Type") {\n')
    for i in range(len(torsion)):
        foutput.write('    @dihedral:%s-%s-%s-%s @atom:*_b*_a*_d%s_i* @atom:*_b*_a*_d%s_i* @atom:*_b*_a*_d%s_i* @atom:*_b*_a*_d%s_i*' %
                (torsion[i][0], torsion[i][1], torsion[i][2], torsion[i][3], torsion[i][0], torsion[i][1], torsion[i][2], torsion[i][3]))
    foutput.write('  } # end of dihedrals\n\n')

### Improper Info ###
# Incomplete
ieconv = econv # improper coeff conversion
if improp_flag:
    if istyle == '':
        sys.stderr.write('Warning: no improper potential provided, assuming harmonic\n')
        istyle == 'harmonic'
    foutput.write('  write_once("In Settings") {\n')
    foutput.write('    # ----- Impropers -----\n')
    # As discussed, a check for convention of impropers is probably needed here
    for i in range(len(improp)):
        foutput.write('    improper_coeff @improper:%s-%s-%s-%s %s %f %f\n' %
                (improp[i][0], improp[i][1], improp[i][2], improp[i][3], istyle,
                float(improp[i][4]), float(improp[i][5])))
    foutput.write('  }\n\n')
    foutput.write('  write_once("Data Impropers By Type") {\n')
    for i in range(len(improp)):
        foutput.write('    @improper:%s-%s-%s-%s @atom:*_b*_a*_d*_i%s @atom:*_b*_a*_d*_i%s @atom:*_b*_a*_d*_i%s @atom:*_b*_a*_d*_i%s' %
                (improp[i][0], improp[i][1], improp[i][2], improp[i][3], improp[i][0], improp[i][1], improp[i][2], improp[i][3]))
    foutput.write('  } # end of impropers\n\n')

### Initialization Info ###
sys.stderr.write('Warning: Attempting to write generic "In Init" section,\n'+
                 '         Further modification after this script is extremely likely.\n')
WriteInit()

sys.stderr.write('Warning: The EQUIVALENCES section of the PRM files may have been converted\n'
      '         incorrectly.  Please check the "replace {}" statements for validity.\n'
      '         (This conversion script has only been tested on a couple force fields\n'
      '         which use a specific format.  You must verify the conversion.)\n')
foutput.write('} # %s\n' % ffname[0])
sys.exit()
