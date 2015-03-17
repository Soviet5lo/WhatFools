#!/usr/bin/env python

VERSION = 1.0

import copy
import getopt
import os
import random
import string
import sys
import types
import whrandom

rand = whrandom.whrandom()

### Constants

#Some magic constants. These are multipliers which allow you to tweak
#the scoring system and the difficulty of the game.
GOLD_CONSTANT = 7 #Relative NetHack point value of WFTM gold
ITEM_CONSTANT = 1 #Relative "usefulness" of WFTM item points 
MONSTER_TOUGHNESS_CONSTANT = 7 #Relative maximum difficulty of monsters
MAX_DUNGEON_LEVEL = 65 #Level the player must descend to to win the game
                       #(amulet is on 50)
SCORE_MULTIPLIER = .5   #Monster point value = monster HP * dungeon level-dependent number * this
HEALING_PER_TURN = 50.0/8

#Alignments
LAWFUL = 0
NEUTRAL = 1
CHAOTIC = 2

alignmentMap = { LAWFUL: 'Lawful',
                 NEUTRAL: 'Neutral',
                 CHAOTIC: 'Chaotic'
                 }
alignments = (LAWFUL, NEUTRAL, CHAOTIC)

alignmentSelection = { 'l' : LAWFUL,
                       'n' : NEUTRAL,
                       'c' : CHAOTIC }

#Type of prayers
INTERCESSORY_PRAYER = 'help'
SACRIFICIAL_PRAYER = 'sacrifice'
BLESSING_PRAYER = 'blessing'

GENERIC_HELP_PRAYERS = [ '"Oh mighty %s, hear my plea..."',
                         '"Dear %s, I need your help."',
                         '"Help me, %s!"',
                         '"HELP!"',
                         '"Hey, %s, how about a hand for your chosen one..."',
                         '"%s, if you help me out here I\'ll never ask you for anything again..."',
                         '"%s, you are generous and wise, your virtue far surpassing that of all other gods..."',
                         ]

GENERIC_SACRIFICE_PRAYERS = [ '"O %s, accept this humble sacrifice..."',
                              '"Accept this sacrifice into your heavens, oh %s..."']


GENERIC_BLESSING_PRAYERS = [ '"O great and powerful %s, I crave a boon."',
                             '"%s, I beseech thee, bestow upon me some sign of favor."' ]

class Role:
    def __init__(self, key, name, pluralName, title,
                 alignmentRestrictions = None, raceRestrictions=None,
                 greeting = "Hello"):
        self.key = key

        self.greeting = greeting

        if type(name) == types.StringType:
            self.names = (name, name)
        else:
            self.names = name

        self.pluralName = pluralName

        if type(title) == types.StringType:
            self.titles = (title, title)
        else:
            self.titles = title

        if type(alignmentRestrictions) == types.StringType:
            alignmentRestrictions = [alignmentRestrictions]

        if type(raceRestrictions) == types.StringType:
            raceRestrictions = [raceRestrictions]

        self.alignmentRestrictions = alignmentRestrictions
        self.raceRestrictions = raceRestrictions

roles = [
    Role('a', 'Archaeologist', 'Archaeologists', 'Digger',
               [LAWFUL, NEUTRAL]),
    Role('b', 'Barbarian', 'Barbarians', ('Plunderer', 'Plunderess'),
               [NEUTRAL, CHAOTIC], ['human', 'orc']),
    Role('c', ('Caveman', 'Cavewoman'), 'Cavemen', 'Troglodyte',
               [LAWFUL, NEUTRAL]),
    Role('h', 'Healer', 'Healers', 'Rhizotomist', NEUTRAL),
    Role('k', 'Knight', 'Knights', 'Gallant', LAWFUL, 'human', 'Salutations'),
    Role('m', 'Monk', 'Monks', 'Candidate', None, 'human'),
    Role('p', ('Priest', 'Priestess'), None, 'Aspirant'),
    Role('r', 'Ranger', 'Rangers', 'Tenderfoot', [NEUTRAL, CHAOTIC]),
    Role('R', 'Rogue', 'Rogues', 'Footpad', CHAOTIC, ['human', 'orc']),
    Role('s', 'Samurai', 'Samurai', 'Hatamoto', LAWFUL, 'human', 'Konnichi wa'),
    Role('t', 'Tourist', 'Tourists', 'Rambler', NEUTRAL, 'human', 'Aloha'),
    Role('v', (None, 'Valkyrie'), 'Valkyries', 'Stripling',
               [LAWFUL, NEUTRAL], ['human', 'dwarf']),
    Role('w', 'Wizard', 'Wizards', 'Evoker', [NEUTRAL, CHAOTIC], ['human', 'elf', 'orc'])
    ]

roleMap = {}
for role in roles:
    roleMap[role.key] = role

raceData = {
    'human' : [LAWFUL, NEUTRAL, CHAOTIC],
    'dwarf' : [LAWFUL],
    'elf' : [CHAOTIC],
    'gnome' : [NEUTRAL],
    'orc' : [CHAOTIC]   
    }

genderData = {
    'male' : ('he', 'him', 'his'),
    'female' : ('she', 'her', 'her')
}

gods = {
    'a' : ('Quetzalcoatl', 'Camaxtli', 'Huhetotl'),
    'b' : ('Mitra', 'Crom', 'Set'),
    'c' : ('Anu', 'Ishtar', 'Anshar'),
    'h' : ('Athena', 'Hermes', 'Poseidon'),
    'k' : ('Lugh', 'Brigit', 'Manannan Mac Lir'),
    'm' : ('Shan Lai Ching', 'Chih Sung-tzu', 'Huan Ti'),
    'r' : ('Mercury', 'Venus', 'Mars'),
    'R' : ('Issek', 'Mog', 'Kos'),
    's' : ('Amaterasu Omikami', 'Raijin', 'Susanowo'),
    't' : ('Blind Io', 'The Lady', 'Offler'),
    'v' : ('Tyr', 'Odin', 'Loki'),
    'w' : ('Ptah', 'Thoth', 'Anhur')
    }

### Stuff copied from the Python Cookbook

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError: pass
        self.impl = _GetchUnix()
        
    def __call__(self): return self.impl()
        
class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        if hasattr(termios, 'TCSADRAIN'):
            iomod = termios
        else:
            import TERMIOS
            iomod = TERMIOS
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, iomod.TCSADRAIN, old_settings)
            return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt
        
        def __call__(self):
            import msvcrt
            return msvcrt.getch()
        
getch = _Getch()

### The game proper

class Game:

    def cls(self):
        #NOTE: Nothing will happen on other systems
        if os.name == 'posix':
            os.system('clear')
        elif os.name in ('nt', 'dos'):
            os.system('cls')
    
    def wrap(self, s, width=78):
        "Copied from the Python Cookbook. Written by Mike Brown."
        return reduce(lambda line, word, width=width: "%s%s%s" % 
                      (line,
                       ' \n'[(len(line[string.rfind(line, '\n')+1:]) + 
                              len(word) >= width)], word),
                      string.split(s, ' ')
                      )

    def usage(self, exit=1):
        as = alignmentSelection.keys()
        as.sort()
        rs = roleMap.keys()
        rs.sort()
        print 'Usage: %s [-a%s] [-p%s] [-D]' % (sys.argv[0],
                                                string.join(as, ''),
                                                string.join(rs, ''))
        sys.exit(exit)

    def getCharacter(self, validCharacters=None, prompt=None, allowQuit=0):
        "Stolen from Python cookbook."
        if prompt:
            print prompt, ' ', 
        if allowQuit:
            if validCharacters:
                if string.find(validCharacters, 'q') == -1:
                    validCharacters = validCharacters + 'q'
            else:
                validCharacters = 'q'
        input = getch()
        while validCharacters and string.find(validCharacters, input) == -1:
            input = getch()
        if allowQuit and string.lower(input) == 'q':
            sys.exit()
        return input
    
    def getYesNo(self, message, allowQuit=0):
        valid = 'yn'
        if allowQuit:
            valid = valid + 'q'
        result = self.getCharacter(valid, message + ' [%s]' % valid, 1)
        if (result == 'q'):
            sys.exit()
        else:
            return (result == 'y')            

    def more(self, indent=0):
        print ('' * indent) + '--More--',
        self.getCharacter()

    def run(self, argv):
        self.god = self.obtainGod(argv)
        self.pc = self.god.getWorshipper()
        self.cls()
        self.printIntro()
        self.cls()
        self.play()

    def splashScreen(self):
        self.cls()
        print 'What Fools These Mortals, Copyright 2003'
        print '                          By Leonard Richardson.'
        print '                          See license for details.'
        print

    def obtainGod(self, argv):
        self.discovery = 0
        self.role = None
        self.alignment = None
        self.collectInfoFromOptions(argv)
        if self.role == None or self.alignment == None:
            self.splashScreen()
            self.collectInfoFromUser()
        return God(self, self.role, self.alignment)

    def collectInfoFromOptions(self, args):
        selectionMap = { 'p' : ('role', roleMap),
                         'a' : ('alignment', alignmentSelection) }
        try:
            optlist, args = getopt.getopt(args[1:], 'a:p:D')
        except getopt.error:
            self.usage()
        for (opt, val) in optlist:
            opt = opt[1]
            if opt == 'D':
                self.discovery = 1
            t = selectionMap.get(opt)
            if t:
                name, map = t
                if not map.has_key(val):
                    values = map.keys()
                    values.sort()
                    raise ValueError, 'Invalid value "%s" for -%s; valid values are: %s' % (val, opt, string.join(values, ''))
                setattr(self, name, map[val])

    def collectInfoFromUser(self):
        indent = ' ' * 35
        whatToPick = 'a deity for you'
        if self.alignment:
            whatToPick = 'a role for your deity'
        elif self.role:
            whatToPick = 'an alignment for your deity'
        pick = self.getYesNo('Shall I pick %s?' % whatToPick, 1)
        if pick:
            if self.alignment == None:
                self.alignment = rand.choice(alignments)
            if self.role == None:
                while not self.role or not self.role.pluralName:
                    self.role = random.choice(roles)
        else:
            if self.role == None:
                self.cls()
                print 'Choose the profession from which you draw worshippers.'
                acceptableRoles = []
                for role in roles:
                    if role.pluralName:
                        print indent, '%s - %s' % (role.key, role.pluralName)
                        acceptableRoles.append(role.key)
                print indent, '* - Random'
                print indent, 'q - Quit'
                acceptableChars = '*q' + string.join(acceptableRoles)
                key = self.getCharacter(acceptableChars, indent+ ' (end)')
                if key == 'q':
                    sys.exit()
                if key == '*':
                    key = random.choice(acceptableRoles)
                self.role = roleMap[key]

            if self.alignment == None:
                acceptableKeys = []
                self.cls()
                indent = ' ' * 9
                print 'Choose an alignment.'
                for i in alignments:
                    alignment = alignmentMap[i]
                    key = string.lower(alignment[0])
                    acceptableKeys.append(key)
                    print indent, '%s - %s' % (key, alignment)
                print indent, '* - Random'
                print indent, 'q - Quit'
                acceptableChars = '*q' + string.join(acceptableKeys)
                key = self.getCharacter(acceptableChars, indent+' (end)')
                if key == 'q':
                    sys.exit()
                if key == '*':
                    key = random.choice(acceptableKeys)
                for (align, name) in alignmentMap.items():
                    if string.lower(name[0]) == key:
                        self.alignment = align
                        break            

    def printIntro(self):
        print """It is written in your most sacred book:

   After the Creation, the cruel god Moloch rebelled against the
   authority of Marduk the Creator.  Moloch stole from Marduk the most
   powerful of all the artifacts of the gods, the Amulet of Yendor,
   and he hid it in the dark cavities of Gehennom, the Under World,
   where he now lurks, and bides his time."""

        print
        print self.wrap("You seek to possess the Amulet, and with it to gain deserved ascendance over the other gods.")
        print

        print self.wrap("One young %s, now a newly trained %s, has been heralded from birth as your instrument.  %s is destined to recover the Amulet for you, or die in the attempt.  %s hour of destiny has come.  May %s go bravely with you!" % (self.pc.race, self.pc.title, self.pc.He, self.pc.His, self.pc.he))
        print
        self.more()

    def play(self):
        sys.stdout.write("%s, %s, %s protector of %s.\n" % (self.god.role.greeting, self.god.name, self.god.alignmentName, self.god.role.pluralName))
        print "Your chosen one has just entered the dungeon.\n...\n"
        while self.pc.alive():
            self.pc.turn()
        if self.pc.won:
            end = "sacrificing the Amulet"
        elif self.pc.quit:
            print "What the?!? Your chosen one just quit %s quest!" % self.pc.his
            print "All the other gods laugh at you."
            end = "quitting"
        else:
            end = "dying"            
            self.pc.score = int(self.pc.score * .9)
            print "Argh! Your chosen one just died!"            
            print "All the other gods laugh at you."
        print
        self.more()
        print
        print
        pluralScore = 's'
        if self.pc.score == 1:
            pluralScore = ''
        print "Your chosen one scored %s point%s before %s." % (self.pc.score, pluralScore, end)
        if (self.pc.quit):
            print 'Because %s quit, you get none of that.' % self.pc.he
        else:
            print "Your tithe of that is %s points." % int(self.pc.score * .1)

class God:

    """
        "Do not create god classes/objects in your systems."
            --Arthur J. Reil, "Object-Oriented Design Heuristics"
              (Heuristic 3.2)
    """

    def __init__(self, game, role, alignment):
        print role, alignment
        self.game = game
        self.role = role
        self.alignment = alignment
        self.alignmentName = alignmentMap[alignment]
        self.name = gods[role.key][alignment]

    def getWorshipper(self):
        return Player(self.game, self.role, self.alignment, self,
                      self.game.discovery)

    def handlePrayer(self, worshipper, type, arg=None):
        if type == INTERCESSORY_PRAYER:
            self.handlePrayerHelp(worshipper, arg)
        elif type == SACRIFICIAL_PRAYER:
            self.handlePrayerSacrifice(worshipper, arg)
        elif type == BLESSING_PRAYER:
            self.handlePrayerBlessing(worshipper)
        print

    def getMood(self, worshipper, troubleLevel):
        """Translates the prayer timout into 1 for pleased, 0 for indifferent,
        and -1 for hostile."""
        if troubleLevel == 1:
            cutoff = 200
        else:
            cutoff = 100

        mood = 1
        if worshipper.prayerTimeout > cutoff:
            mood = -1
        elif worshipper.prayerTimeout > cutoff * .5:
            mood = 0
        return mood

    def handlePrayerHelp(self, worshipper, troubleLevel):
        options = ['[h]elp', '[i]gnore', '[s]mite']
        order = (0,1,2)
        mood = self.getMood(worshipper, troubleLevel)
        if mood > 0:
            print 'Oh no! Your chosen one is praying for help!'
        elif mood == 0:
            print 'Sounds like %s needs some help.' % worshipper.he
            order = (1,0,2)
        else:            
            print 'That %s is praying for help!' % worshipper.getEpithet()
            order = (2,1,0)
        what = 'Do you want to '
        a = 0
        for i in order:
            what = what + options[i]
            a = a + 1
            if a == len(options)-1:
                what = what + ', or '
            elif a < len(options):
                what = what + ', '
        what = what + ' ' + worshipper.him + '?'
        print self.game.wrap(what)
        key = self.game.getCharacter('his', allowQuit=1)
        if key == 'h':
            print 'Okay, you send a generic healing blessing %s way.' % worshipper.his
            worshipper.hp = worshipper.maxHP
            worshipper.resetPrayerTimeout()
            if not random.randint(0,30):
                print "Hm, %s died anyway; I guess the healing wasn't what %s needed." % (worshipper.he, worshipper.he)
                worshipper.hp = 0
        elif key == 'i':
            print "Yeah, let 'em deal with it."
            worshipper.hp = worshipper.maxHP / 2
        elif key == 's':
            self.punish(worshipper)

    def handlePrayerSacrifice(self, player, sacValue):
        value = -1
        if sacValue >= player.maxHP * .40:
            value = 1
            print " (Wow, what a great sacrifice! The other gods will be jealous!)"
        elif sacValue >= player.maxHP * .20:
            value = 0
            print " (A pretty decent sacrifice.)"
        else:
            print " (Not that great a sacrifice.)"
        if player.alignment == CHAOTIC:
            multiplier = 500
        else:
            multiplier = 300
        multuplier = float(multiplier)/24
        player.prayerTimeout = max(0, player.prayerTimeout - (sacValue * multiplier))
        if player.prayerTimeout == 0 and (value == 1 or (value == 0 and not random.randint(0, 10))):
            val = self.game.getYesNo('Show some sign of favor?')
            print
            if val:
                self.grantBoon(player)

    def handlePrayerBlessing(self, worshipper):
        options = ['[g]rant %s a boon' % worshipper.him,
                   '[i]gnore %s' % worshipper.him,
                   '[s]mite %s for %s impudence' % (worshipper.him,
                                                    worshipper.his)]
        order = (0,1,2)
        mood = self.getMood(worshipper, 0)
        if mood == 0:
            print 'Hm, pretty presumptuous of %s to ask for help.' % worshipper.him
            order = (1,0,2)
        elif mood < 0:
            print 'That %s has the audacity to ask for your help?' % worshipper.getEpithet()
            order = (2,1,0)
        what = 'Do you want to '
        a = 0
        for i in order:
            what = what + options[i]
            a = a + 1
            if a == len(options)-1:
                what = what + ', or '
            elif a < len(options):
                what = what + ', '
        what = what + '?'
        print self.game.wrap(what)
        key = self.game.getCharacter('gis', allowQuit=1)
        if key == 'g':
            self.grantBoon(worshipper)
            worshipper.resetPrayerTimeout()
        elif key == 'i':
            print "Makes sense; %s should have to do better!" % worshipper.he
        elif key == 's':
            self.punish(worshipper)

    def grantBoon(self, worshipper):
        if worshipper.prayerTimeout < 50 and not random.randint(0, 3):
            print 'Okay, you send some magical junk %s way.' % worshipper.his
            points = random.randint(100, 500)
        else:
            print 'Okay, you bless some of %s junk.' % worshipper.his
            points = random.randint(10, 100)
        worshipper.itemPoints = worshipper.itemPoints + points

    def punish(self, worshipper):
        punishment = random.choice(['zap', 'drain', 'ball', 'curse', 'minion'])
        if punishment == 'zap':
            print 'Hells yeah! Make with the lightning!'
            print '*CRAK*'
            worshipper.costItemPoints(random.expovariate(50))
            worshipper.costHitPoints(random.expovariate(100))
            if worshipper.itemPoints > 0 and worshipper.alive():
                print "Damn! %s didn't even feel it!" % worshipper.He
                print 'Musta had one of those godproof silver dragon scale mails!'
                print 'Perhaps summoning some minions will do the trick...'
                print '*SHAZAM*'
                worshipper.stackedMonsters = 5            
        elif punishment == 'drain':
            print 'All right! Time for some level drain action!'
            print '*WOMP*'
            worshipper.maxHP = worshipper.maxHP * .9
            if worshipper.hp > worshipper.maxHP:
                worshipper.hp = worshipper.maxHP
        elif punishment == 'ball':
            print 'This iron ball and chain should teach %s a lesson!' % worshipper.him
            print '*THRUD*'
            worshipper.costItemPoints(random.randint(10,15))
        elif punishment == 'curse':
            print 'Let %s equipment be blackened with a foul curse!' % worshipper.his
            print '*SHUM*'
            worshipper.costItemPoints(random.randint(20, 50))
        elif punishment == 'minion':
            print 'Your minions will make short work of %s!' % worshipper.him
            print '*SHAZAM*'
            worshipper.stackedMonsters = 5            

    def endgame(self, whoGotAmulet=None):
        if not whoGotAmulet:
            whoGotAmulet = self
        self.game.more()
        self.game.cls()
        amuletProps = ['You get clairvoyance, if it is not blocked.',
                       'When casting spells, your energy is drained.',
                       'Hunger is increased (additional to normal amulet hunger).',
                       'Your luck timeout is increased.',
                       'Monster difficulty will depend on your deepest level reached, not your\n|    current dungeon level.',
                       'Monsters are less likely to be generated asleep.',
                       '...']
        if whoGotAmulet == self:
            sys.stdout.write(self.game.wrap("You feel a rush of power as your chosen one places the Amulet of Yendor on your altar. At last, the Amulet is yours!\n\n"))
            otherGods = list(gods[self.role.key])
            otherGods.remove(self.name)
            print self.game.wrap("You rush to the Hall of Spoilers to review the Amulet's capabilities, already dreaming of primacy over %s and %s." % tuple(otherGods))
            print
            print '| Amulet of Yendor'
            print '|'            
            print '| When carried, you get all of the following (mostly bad):'
            for prop in amuletProps:
                print '|  *', prop                
            print
            print 'Hmm...'
            print
            print self.game.wrap('Perhaps Moloch would be amenable to taking the Amulet back. You begin casting about for another chosen one to carry out this important task...')

class Player:

    def __init__(self, game, role, alignment, god, discovery=0):
        self.game = game
        self.discovery = discovery
        
        self.amulet = 0
        self.won = 0
        self.quit = 0

        self.stackedMonsters = 0 #Monsters sent as part of a punishment.

        self.hp = 15
        self.maxHP = 15
        self.itemPoints = 50

        self.score = 0

        self.turnsOnLevels = {}
        self.turnsOnLevel = 0
        self.setLevel(1)

        self.experienceLevel = 1

        self.nearAltar = 0
        self.prayerTimeout = 300

        self.role = role #This might change later; they might be a priest.
        self.alignment = alignment
        self.god = god

        if self.role.key == 'v':
            self.gender = 'female'
        else:
            self.gender = random.choice(('male', 'female'))
        (self.he, self.him, self.his) = genderData[self.gender]
        self.He = string.capitalize(self.he)
        self.Him = string.capitalize(self.him)
        self.His = string.capitalize(self.his)

        possibleRacesModuloClass = raceData.keys()
        possibleRaces = raceData.keys()
        aRestrict = role.alignmentRestrictions
        rRestrict = role.raceRestrictions

        for race in copy.copy(possibleRaces):
            try:
                classOkay = 0
                raceData[race].index(self.alignment)
                classOkay = 1
                if aRestrict:
                    aRestrict.index(self.alignment)
                if rRestrict:
                    rRestrict.index(race)
            except Exception, val:
                possibleRaces.remove(race)
                if not classOkay:
                    possibleRacesModuloClass.remove(race)
        #If there's only one possible alignment and the player isn't
        #of this alignment, they've got to be a priest.
        if possibleRaces and rand.choice(roleMap.keys()) != 'p':
            self.race = random.choice(possibleRaces)
        else:
            self.role = roleMap['p']
            self.race = random.choice(possibleRacesModuloClass)

        if self.gender == 'male':
            self.title = self.role.titles[0]
        else:
            self.title = self.role.titles[1]

    def turn(self):
        self.turnsOnLevel = self.turnsOnLevel + 1
        if self.prayerTimeout > 0:
            self.prayerTimeout = max(0, self.prayerTimeout - 1)
        self.hp = self.hp + int(HEALING_PER_TURN)
        if self.hp > self.maxHP:
            self.hp = self.maxHP
        self.handleEvent()

    def getEpithet(self):
        choices = ['so-and-so', 'pathetic mortal', 'weakling']
        if self.gender == 'male':
            choices.append('S.O.B')
        return random.choice(choices)

    def getPrayerDescription(self, type):
        if type == INTERCESSORY_PRAYER:
            a = random.choice(GENERIC_HELP_PRAYERS)
        elif type == SACRIFICIAL_PRAYER:
            a = random.choice(GENERIC_SACRIFICE_PRAYERS)
        elif type == BLESSING_PRAYER:
            a = random.choice(GENERIC_BLESSING_PRAYERS)
        if string.find(a, '%s') != -1:
            a = a % self.god.name
        return a

    def resetPrayerTimeout(self):
        reset = 350
        #TODO: crowning
        if self.amulet:
            reset = reset + 100
        self.prayerTimeout = random.expovariate(reset)

    def setLevel(self, level):
        self.turnsOnLevels[level] = self.turnsOnLevel
        self.dungeonLevel = level
        self.turnsOnLevel = self.turnsOnLevels.get(level, 0)

    def alive(self):
        return self.hp > 0 and not self.quit and not self.won

    def handleEvent(self):
        happened = 0
        if self.stackedMonsters:
            self.stackedMonsters = self.stackedMonsters - 1
        else:
            for event in self.EVENTS:
                chance = self.__class__.__dict__[event+'Chance'](self)
                if chance > 0 and not random.randint(0, chance):
                    happened = not self.__class__.__dict__[event](self)
                    if happened:
                        break
        if not happened:
            self.fightMonster()

    EVENTS = [ 'getGoodie', 'descendLevel', 'findAltar', 'ascendLevel',
               'loseAltar' ]

    def ascendLevelChance(self):
        return 100

    def ascendLevel(self):
        if self.dungeonLevel == 1 or self.dungeonLevel >= MAX_DUNGEON_LEVEL - 1:
            return 1
        self.setLevel(self.dungeonLevel-1)

    def descendLevelChance(self):
        return max(5, 100-self.turnsOnLevel)
    
    def descendLevel(self):
        self.setLevel(self.dungeonLevel+1)
        if random.randint(1,4) == 1:
            self.nearAltar = 0
        if self.dungeonLevel == 50:
            self.getAmulet()
        if self.dungeonLevel == MAX_DUNGEON_LEVEL - 1:
            print "You sense your chosen one's presence on the Astral Plane..."
            print
        if self.dungeonLevel == MAX_DUNGEON_LEVEL and self.amulet:
            self.endgame()

    def findAltarChance(self):
        return max(300, 150+self.turnsOnLevel)

    def findAltar(self):
        self.nearAltar = 1
        if not random.randint(0, 3):
            self.pray(BLESSING_PRAYER)

    def loseAltarChance(self):
        return 100

    def loseAltar(self):
        if self.nearAltar:
            self.nearAltar = 0
            return 0
        return 1

    def getGoodieChance(self):
        return 20 + (self.turnsOnLevel/5)

    def getAmulet(self):
        if not self.amulet:
            self.amulet = 1
            print '%s got the Amulet! Awesome!\n' % self.He

    def endgame(self):
        self.won = 1
        print self.game.wrap('"Oh %s, your humble servant offers to your glory the object of this sacred quest..."' % self.god.name)
        self.god.endgame()

    def getGoodie(self):
        value = random.randint(0, max(self.dungeonLevel, int(1.5*self.dungeonLevel)-self.turnsOnLevel))
        if not random.randint(0, 3):
            #Gold; includes amortized value of gold from items sold at shops
            self.score = self.score + value * GOLD_CONSTANT
        elif random.randint(0, 5): #Something useful
            self.itemPoints = self.itemPoints + int(value * ITEM_CONSTANT)
            if self.nearAltar and not random.randint(0, 20):
                self.pray(BLESSING_PRAYER)

        #Otherwise, it's useless junk

    def fightMonster(self):
        toughness = (random.randint(0,6)-3) + self.dungeonLevel/2
        if toughness < 0:
            toughness = 1
        monsterHP = random.randint(toughness,
                                   toughness*MONSTER_TOUGHNESS_CONSTANT)
        maxMonsterHP = monsterHP
        value = monsterHP
        if monsterHP < 1:
            monsterHP = 1
        while monsterHP > 0 and self.alive():
            #You attack
            done = 0
            if self.hp < 5:
                if self.discovery:
                    quitChance = 20
                else:
                    quitChance = 4
                if random.randint(0, quitChance):
                    self.pray('help', random.randint(1,3))
                    done = 1                
                else:
                    self.quit = 1
                    done = 1
            if not done:
                multiplier = 1
                if not random.randint(0, 3):
                    #Miss
                    multiplier = 0
                elif self.itemPoints > 0 and random.randint(0, 3):
                    #More damage, but also some loss of item points
                    multiplier = int(random.random() * 10)
                else:
                    multiplier = 1
                if multiplier > 1:
                    if not self.costItemPoints(multiplier * random.randint(1,4)):
                        multiplier = 1
                damage = random.randint(3,self.dungeonLevel+3) * multiplier
                monsterHP = monsterHP - damage
            
            #Monster attacks
            if monsterHP > 0:
                damage = 0
                if not random.randint(0, 3):
                    #Miss
                    pass
                else:
                  damage = random.randint(0, toughness)
                #Chance of you giving up item points to absorb damage.
                if not random.randint(0, 2):
                    multiplier = random.randint(2,10)
                    #a = self.itemPoints
                    if self.costItemPoints(multiplier / random.randint(1,4)):
                        #print "%s->%s" % (a, self.itemPoints)
                        damage = int(damage * (float(multiplier)/multiplier+1))
                self.hp = self.hp - damage
                if self.discovery and self.hp <= 0:
                    self.hp = self.maxHP

        if self.alive():
            #Pet logic, bleah
            self.score = self.score + int(value * (self.dungeonLevel * (self.dungeonLevel * .04) * SCORE_MULTIPLIER))
            self.hp = self.hp + 1
            self.maxHP = self.maxHP + 1
            if self.nearAltar and not random.randint(0,3):
                self.pray('sacrifice', maxMonsterHP)
            if not random.randint(0, 4):
                self.getGoodie() #Woohoo            

    def costItemPoints(self, cost):
        if self.itemPoints > 0:
            self.itemPoints = max(0, self.itemPoints-cost)
            return 1
        self.itemPoints = 0

    def costHitPoints(self, cost):
        if self.hp > 0:
            self.hitPoints = max(0, self.hp-cost)
            return 1
        self.hp = 0

    def pray(self, type, arg=None):
        print self.game.wrap(self.getPrayerDescription(type))
        self.god.handlePrayer(self, type, arg)
                    
if __name__ == '__main__':
    Game().run(sys.argv)
