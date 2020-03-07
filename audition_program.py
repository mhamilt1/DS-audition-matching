# Modification of Gale-Shapley algorithm to match dancers into pieces 
# based on mutual preferences
# Run: python audition_program.py <choreo-rankings.cvs> <dancer-rankings.csv> <sign-in.csv>
# Ensure there's a directory "piece_assignments" to put assignments in
# TO-DO: Clean up style (documentation, inputs/return types, variable names (camelCase))
# TO-DO: Add README with file formats (+ trouble-shooting: make sure no commas in .csv files)

import argparse, csv

printOUT_PATH = 'piece_assignments/'
parser = argparse.ArgumentParser()
parser.add_argument('choreographer_prefs') #path to the choreographers' rankings file (.csv)
parser.add_argument('dancer_prefs') #path to the dancers' rankings file (.csv)
parser.add_argument('sign_in') #path to sign in sheet (.csv)
args = parser.parse_args()

# Piece rankings: list of tuples (piece ID, dancer's ranking), sorted by dancer's ranking
# Pieces: set of pieces dancer is in with capacity num_pieces
class Dancer(object):
	def __init__(self, first_name, last_name, audition_number, 
				gender, num_pieces, piece_rankings, email, phone):

		self.first_name = first_name
		self.last_name = last_name
		self.audition_number = audition_number
		self.gender = gender
		self.num_pieces = num_pieces
		self.piece_rankings = piece_rankings
		self.email = email
		self.phone = phone
		self.pieces = {}

	def __repr__(self):
		return "%d %s %s %s %s %s" % (self.audition_number, ";", 
			self.first_name, self.last_name, ";", self.email)

# Gender constraint: if non-empty, dict with key: 'M'/'F' with val: int to indicate gender
# constraint, else: no constraint preferred
# Dancer rankings: dict of choreorapher's dancer preferences, key: dancer ID, val: 
# choreographer's dancer preference (rank)
# Dancers: set of dancers currently in piece
# Alternates: set of dancers who may later join the piece (in the case of gender constraints)
class Piece(object):
	def __init__(self, piece_id, choreographer_name, 
				capacity, gender_constraint, dancer_rankings):

		self.piece_id = piece_id
		self.choreographer_name = choreographer_name
		self.capacity = capacity
		self.gender_constraint = gender_constraint
		self.dancer_rankings = dancer_rankings
		self.dancers = {}
		self.alternates = {}

	def __repr__(self):
		return str(self.choreographer_name) + ": " + str(self.piece_id)

#turns CSV into map of pieces (key: piece id (1,2,...), val: Piece object)
def csvToPieces(choreographerPrefFile):
	choreoPrefs = open(choreographerPrefFile, 'r')
	choreoPrefsHeaders = ['id', 'name', 'total', 'num_males', 'num_females']
	pieceMap = {}

	for i, line in enumerate(choreoPrefs):
		if i == 0: continue

		column = line.strip().split(',')
		piece_id = (column[choreoPrefsHeaders.index('id')])
		name = column[choreoPrefsHeaders.index('name')]
		total = int(column[choreoPrefsHeaders.index('total')])
		num_males = int(column[choreoPrefsHeaders.index('num_males')])
		num_females = int(column[choreoPrefsHeaders.index('num_females')])

		gender_constraint = {}
		if num_males + num_females == total:
			gender_constraint['F'] = num_females
			gender_constraint['M'] = num_males

		preferences = column[len(choreoPrefsHeaders):]
		rankings = {} #rank is 0 if definite, >1 if alternate
		for rank, audition_num in enumerate(preferences):
			if audition_num == '':
				break
			if rank < total:
				rankings[int(audition_num)] = 0
			else:
				rankings[int(audition_num)] = rank - total +1
		pieceMap[piece_id]  = Piece(piece_id, name, total, gender_constraint, rankings)

	choreoPrefs.close()

	return pieceMap

#turns CSV into map of dancers (key: audition num, val: Dancer object)
def csvToDancers(dancerPrefsFile, signInFile):
	dancerInfo = open(signInFile, 'r')
	dancerInfoHeaders = ['time', 'audition_number', 
				'last_name', 'first_name', 'class', 
				'email', 'num_semesters', 'phone']
	contactMap = {}

	for i,line in enumerate(dancerInfo):
		if i == 0: continue

		column = line.strip().split(',')
		audition_number = int(column[dancerInfoHeaders.index('audition_number')])
		email = column[dancerInfoHeaders.index('email')]
		phone = column[dancerInfoHeaders.index('phone')]
		contactMap[audition_number] = (email, phone)

	dancerInfo.close()

	dancerRankings = open(dancerPrefsFile, 'r')
	dancerRankingsHeaders = ['time', 'first_name', 'last_name', 
							'audition_number', 'gender', 'num_pieces']
	dancerMap = {}

	for i,line in enumerate(dancerRankings):
		if i == 0: continue

		column = line.strip().split(',')
		first_name = column[dancerRankingsHeaders.index('first_name')]
		last_name = column[dancerRankingsHeaders.index('last_name')]
		audition_number = int(column[dancerRankingsHeaders.index('audition_number')])
		gender = column[dancerRankingsHeaders.index('gender')]
		num_pieces = int(column[dancerRankingsHeaders.index('num_pieces')])

		preferences = column[len(dancerRankingsHeaders):-1]
		ranking_tuples = [(piece, int(ranking)) 
			for piece,ranking in enumerate(preferences) if ranking != ""]
		sorted_rankings = sorted(ranking_tuples, key=lambda tup: tup[1])
		piece_rankings = [(str(dance_index+1), ranking) 
			for (dance_index, ranking) in sorted_rankings]

		(email, phone) = contactMap.get(audition_number, ('no email', 'no phone'))

		dancerMap[audition_number] = Dancer(first_name, last_name, 
									audition_number, gender, num_pieces, 
									piece_rankings, email, phone)
	dancerRankings.close()

	return dancerMap

#checks if certain piece ranked a certain dancer
def checkIfPieceRankedDancer(piece, dancer):
	dancer_id = dancer.audition_number
	rankings = piece.dancer_rankings
	if dancer_id in rankings:
		return True
	return False

# return dancer's least fave piece (worstID, worstRank)
# note: (piece, rank) = (x, int)
def findWorstPiece(dancer):
	worstRank = 0
	worstID = None

	for (piece, rank) in dancer.piece_rankings:
		if piece in dancer.pieces and rank > worstRank:
			worstID, worstRank = piece, rank
		if (piece + "M") in dancer.pieces and rank > worstRank:
			worstID, worstRank = (piece + "M"), rank
		if (piece + "F") in dancer.pieces and rank > worstRank:
			worstID, worstRank = (piece + "F"), rank
	
	return (worstID, worstRank)

# check if a dancer wants to add this piece to their pieces 
# return: (False, None, None) if we can't add (dancer rejects proposal)
# (True, rank, None): rank = rank of added piece or None if dancer wasn't removed from a piece
# (True, rank, removedPiece): rank = rank of added piece, 
# and removedPiece = piece ID of the piece dancer left
def checkCanAddDancerToPiece(piece, dancer):
	# possible piece: (piece, rank)
	# gets rank of current piece in dancer's rankings
	pieceRank = 1000
	actual_piece = piece.piece_id
	if 'F' in actual_piece or 'M' in actual_piece:
		actual_piece = actual_piece[:-1]

	for possiblePiece in dancer.piece_rankings:
		if possiblePiece[0] == actual_piece:
			pieceRank = possiblePiece[1]
			break

	if pieceRank == 1000:
		return (False, None, None)

	# check if dancer has room to add
	if len(dancer.pieces) < dancer.num_pieces:
		return (True, pieceRank, None)

	# dancer is at max number of pieces, checks if they want to drop a piece
	else:
		(worstID, worstRank) = findWorstPiece(dancer)
		if worstRank > pieceRank:
			# curr piece is higher priority, dancer wants to drop their worst piece
			return (True, pieceRank, worstID)

	# dancer doesn't want to add piece (rank not high enough)
	return (False, None, None)

# gets next dancer for piece to propose to
def findDancer(piece):
	dancers = []
	for key in piece.dancer_rankings:
		dancers.append((key,piece.dancer_rankings[key]))
	sortedDancers = sorted(dancers, key = lambda x:x[1])

	if sortedDancers == []:
		return None

	dancer_id = sortedDancers[0][0]

	return dancer_id

# check if all pieced filled or, if unfilled, then all dancers in that piece were proposed to
def checkAllProposed(pieces):
	for pieceID in pieces:
		piece = pieces[pieceID]
		if len(piece.dancers) < piece.capacity:
			# piece unfilled
			if len(piece.dancer_rankings) != 0:
				# unfilled piece didn't finish proposing
				return False

	# all pieces filled + unfilled pieces proposed to all
	return True

# outputs pieces to .txt files
def writePieces(pieces):
	for pieceID in pieces:
		piece = pieces[pieceID]
		pieceFile = open(printOUT_PATH + '%s - %s.txt' % (piece.piece_id, 
							piece.choreographer_name.replace('/', '_')), 'w')
		pieceFile.write('********************\n')
		pieceFile.write('%s (%s) \n' % (piece.choreographer_name, piece.piece_id))

		pieceFile.write('********************\n')
		dancers = []
		for dancerID in piece.dancers:
			dancers.append(dancerID)
		sortedDancers = sorted(dancers)
		for dancerID in sortedDancers:
			dancerStr = piece.dancers[dancerID]
			pieceFile.write(str(dancerStr) + '\n')

		pieceFile.close()
	return

# writes list of dancers who were successfully assigned into piece(s) to .csv file
def makeAssigned(pieces):
	assignedFile = open(printOUT_PATH + "assigned.csv", 'w')
	for pieceID in pieces:
		piece = pieces[pieceID]
		assignedFile.write(str(piece) + '\n')
		dancers = []
		for dancerID in piece.dancers:
			dancers.append(dancerID)
		sortedDancers = sorted(dancers)
		for dancerID in sortedDancers:
			dancerStr = piece.dancers[dancerID]
			assignedFile.write(str(dancerStr) + '\n')

	assignedFile.close()
	return

# outputs list of dancers not assigned to a piece to .csv file
def makeUnassigned(dancers):
	unassignedFile = open(printOUT_PATH + 'unassigned.csv', 'w')
	for dancerID in dancers:
		dancer = dancers[dancerID]
		if len(dancer.pieces) == 0:
			unassignedFile.write('%d\t%s\t%s\t%s\t%s\n' % (dancer.audition_number,
                                                dancer.first_name + " " + dancer.last_name,
                                                dancer.gender,
                                                dancer.email,
                                                dancer.phone))

	unassignedFile.close()
	return

def main():
	pieces = csvToPieces(args.choreographer_prefs)
	dancers = csvToDancers(args.dancer_prefs, args.sign_in)

	while (not checkAllProposed(pieces)):
		for pieceID in pieces:
			piece = pieces[pieceID]
			while len(piece.dancers) < piece.capacity and len(piece.dancer_rankings) != 0:
				# propose to dancer
				dancerID = findDancer(piece)
				
				if dancerID != None:

					#print dancerID
					dancer = dancers[dancerID]

					# check if dancer accepts proposal
					(res, pieceRank, removedID) = checkCanAddDancerToPiece(piece, dancer)

					if res:
						# dancer can be added to current piece
						# add dancer to accepted piece
						piece.dancers[dancerID] = dancer

						if removedID == None:
							# dancer isn't leaving a piece, add piece to dancer's list
							dancer.pieces[piece.piece_id] = pieceRank

						else:
							# dancer leaving removedID piece
							leavingPiece = pieces[removedID]

							# remove rejected piece from dancer's list
							dancer.pieces.pop(removedID)

							# add accepted piece to dancer's list
							dancer.pieces[piece.piece_id] = pieceRank

							# remove dancer from rejected piece
							leavingPiece.dancers.pop(dancerID)

					# remove curr dancer from proposal list
					piece.dancer_rankings.pop(dancerID)

	writePieces(pieces)
	makeAssigned(pieces)
	makeUnassigned(dancers)

main()