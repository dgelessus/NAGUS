# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2022 dgelessus
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Provides some cheesy quips for when a client/server error is displayed."""


generic_crash_lines = [
	# Source: OpenUru Discord, #code-dev
	# https://discord.com/channels/282045216221822978/282046743338811392/903679070791946310
	# (with a few minimal spelling adjustments)
	
	# Briggs (who started all of this)
	"What have you done?!",
	# Adam {Hoikas}
	"What kind of fool are you?!",
	# Harley (Calum/Kelsei)
	"Did someone touch the Flux Capacitor!?",
	"Unexpected Bahro encounter.",
	"Someone turned off the Paradox Inhibitor, didn't they?",
	"Who ya gonna call? The Developers, I guess.",
	"Ran out of Pixie Dust.",
	"Needs Faith, trust, and Pixie Dust, and we just ran out of Pixie Dust.",
	"Don't forget your honorary traffic cones!",
	"Eddie popped a seam and needs patching.",
	"Quabs to the left of me, Bahro to the right, and here I am...",
	"Zandi left the grill running. Someone get a fire extinguisher!",
	"Game dev isn't like building model kits, you know. We don't have instructions!",
	"WOHBA! Something went wrong! (:O",
	"Don't make me tap the sign...",
	"We're off to see the Wizard, the wonderful Wizard of D'ni...",
	"Try moving the slider... No no! The amplitude...!",
	"At least it wasn't a net 2, right?",
	# dgelessus
	"This game contains content from Peter Gabriel which is not available in your country. Sorry about that.",
	"🦆'ni needed MEEE!",
	"OOPSIE WOOPSIE!! The explorer is stucky wucky! Our code mangrees are working VERY HAWD to fix this!",
	# chinamicah
	"Sirrus wuz here",
	"Quick, pull the plug! Gehn's trying to escape!",
	# DapperAndy
	"Wait, this is an error? --- ALWAYS HAS BEEN.",
	# roblabla
	"The princess is in another Age.",
	# Zaroth (originally from some YouTubers: https://www.youtube.com/user/RunButton)
	# https://discord.com/channels/282045216221822978/282045216221822978/985189046592622603
	"Many Bothans died to get us a working online version of Uru!",
	
	# More nonsense by yours truly
	"Welcome. To. MystOnlineCom.",
	"You know how hard it is to finish a book with a constant stream of people... interrupting?",
	"Aw, another one!",
	"Now shut up and make it so you only have to jump once.",
	"Breathtaking, isn't it?",
	"2 plus 3 is ... ... ... 10. ... IN BASE FIVE. I'M FINE!",
	"Which brings me to the point of all of this.",
	"You remember Guildsman Efanis. He perished during the construction of the shaft to the surface.",
	"ZZZZZWHAP!",
	"*poofs*",
	"You're really doing this, aren't you?",
	"Tripped over the Maintainer mark.",
	"Is your refrigerator running?",
	"Cho...?",
	"SCREEEECH!",
	"Please don't drink the lake water.",
	"Did the quabs respawn again?!",
	"Well, what did you see?",
	"Everything is fixed now.",
	"45, 289, 32",
	"Nah",
	"You should try our sister game, MUOLa!",
	"Cautious optimism!",
	"Oh bother.",
	"Instructions unclear, Relto book stuck in KI dispenser",
]


client_crash_lines = generic_crash_lines + [
	# Source: OpenUru Discord, #code-dev (see above)
	
	# Harley (Calum/Kelsei)
	"Your KI encountered a serious Error and needed to forcibly reboot itself.",
	"See you Uru Explorer.",
	"Four... Fourteen Line... Fourteen Line Call Staaaaaackk...",
	"UwU, what's this? A crash report? Oh Noes!",
	"Am I so out of touch? No, clearly it's the call stack that must be wrong... REPORT IT ANYWAYS!",
	"Lemme guess... Crash on exit?",
	
	# More nonsense by yours truly
	"Found marker: 'Call stack (12 levels, truncated)'",
	"Try deleting TOS.txt?",
	"Player community linked to game engine crash blossoms",
]


server_crash_lines = generic_crash_lines + [
	# Source: OpenUru Discord, #code-dev (see above)
	
	# dgelessus
	"Quab knocked over the server.",
	# chinamicah
	"The Great Zero is down for maintenance. Please try again later.",
	# DapperAndy
	"D'ni's haunted, exorcism in progress. Come back later.",
	
	# More nonsense by yours truly
	"I... am... NAGUS. And I WILL NOT BEE DEEFEEEATED!",
	"Do not touch the operational end of The Vault. Do not look directly at the operational end of The Vault. Do not submerge The Vault in liquid, even partially.",
	"Please insert NAGUS disc 5",
	"Someone needs to kick the server again.",
	"Player community linked to game server crash blossoms",
	"Owch, right in the Lattice!",
]
