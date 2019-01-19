import argparse, csv

printOUT_PATH = 'test_piece_assignments/'
parser = argparse.ArgumentParser()
parser.add_argument('choreographer_prefs') #path to the choreographers' rankings file (.csv)
parser.add_argument('dancer_prefs') #path to the dancers' rankings file (.csv)
parser.add_argument('sign_in') #path to sign in sheet (.csv)
args = parser.parse_args()

class Dancer(object):
	def __init__(self, first_name, last_name, audition_number, gender, num_pieces, piece_rankings, email, phone):
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
		return "%d %s %s %s %s %s" % (self.audition_number, ";", self.first_name, self.last_name, ";", self.email)

class Piece(object):
	def __init__(self, piece_id, choreographer_name, capacity, gender_constraint, dancer_rankings):
		self.piece_id = piece_id
		self.choreographer_name = choreographer_name
		self.capacity = capacity
		self.gender_constraint = gender_constraint
		self.dancer_rankings = dancer_rankings
		# key is dancer id, value is rank 
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
		piece_id = int(column[choreoPrefsHeaders.index('id')])
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
	dancerInfoHeaders = ['time', 'audition_number', 'last_name', 'first_name', 'class', 'email', 'num_semesters', 'phone']
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
	dancerRankingsHeaders = ['time', 'first_name', 'last_name', 'audition_number', 'gender', 'num_pieces']
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
		ranking_tuples = [(piece, int(ranking)) for piece,ranking in enumerate(preferences) if ranking != ""]
		sorted_rankings = sorted(ranking_tuples, key=lambda tup: tup[1])
		piece_rankings = [(dance_index+1, ranking) for (dance_index, ranking) in sorted_rankings]

		(email, phone) = contactMap.get(audition_number, ('no email', 'no phone'))

		dancerMap[audition_number] = Dancer(first_name, last_name, audition_number, gender, num_pieces, piece_rankings, email, phone)
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
def findWorstPiece(dancer):
	worstRank = 0
	worstID = None

	for (piece, rank) in dancer.piece_rankings:
		if piece in dancer.pieces and rank > worstRank:
			worstID, worstRank = piece, rank
	return (worstID, worstRank)

# check if a dancer wants to add this piece to their pieces 
# return: (False, None, None) if we can't add
# (True, rank, None) where rank is rank of added piece & None if dancer wasn't removed from a piece
# (True, rank, removedPiece) where rank is added piece rank & removedPiece is piece ID of the piece dancer left
def checkCanAddDancerToPiece(piece, dancer):
	"""print dancer.first_name + " " + dancer.last_name + ": "
	print str(dancer.pieces) + ", len: " + str(len(dancer.pieces))
	print dancer.num_pieces"""
	# possible piece: (piece, rank)
	# gets rank of current piece in dancer's rankings
	pieceRank = -1
	for possiblePiece in dancer.piece_rankings:
		if possiblePiece[0] == piece.piece_id:
			pieceRank = possiblePiece[1]
			break

	# check if dancer has room to add
	if len(dancer.pieces) < dancer.num_pieces:
		#print "a"
		return (True, pieceRank, None)

	else:
		#print "b"
		(worstID, worstRank) = findWorstPiece(dancer)
		#print "(worstID, worstRank): " + str((worstID, worstRank))
		if worstRank > pieceRank:
			return (True, pieceRank, worstID)

	# dancer doesn't want to add piece (rank not high enough)
	return (False, None, None)

# gets next dancer for piece to propose to
def findDancer(piece):
	dancers = []
	for key in piece.dancer_rankings:
		dancers.append((key,piece.dancer_rankings[key]))
	sortedDancers = sorted(dancers, key = lambda x:x[1])
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
		pieceFile = open(printOUT_PATH + '%s - %s.txt' % (piece.piece_id, piece.choreographer_name.replace('/', '_')), 'w')
		pieceFile.write('********************\n')
		pieceFile.write('%s (%s) \n' % (piece.choreographer_name, piece.piece_id))

		pieceFile.write('********************\n')
		#sortedDancers = sorted(piece.dancers, key=lambda d: d.id)
		dancers = []
		for dancerID in piece.dancers:
			dancers.append(dancerID)
		sortedDancers = sorted(dancers)
		for dancerID in sortedDancers:
			dancerStr = piece.dancers[dancerID]
			pieceFile.write(str(dancerStr) + '\n')

		pieceFile.close()
	return

def makeAssigned(pieces):
	assignedFile = open(printOUT_PATH + "assigned.txt", 'w')
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

def makeUnassigned(dancers):
	unassignedFile = open(printOUT_PATH + 'unassigned.txt', 'w')
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
			while len(piece.dancers) < piece.capacity:
				# propose to dancer
				dancerID = findDancer(piece)
				#print dancerID
				dancer = dancers[dancerID]

				# check if dancer accepts proposal
				(res, pieceRank, removedID) = checkCanAddDancerToPiece(piece, dancer)

				if res:
					# dancer can be added to current piece
					# add dancer to accepted piece
					#print dancer.first_name + " " + dancer.last_name + " is joining " + piece.choreographer_name
					#print str(dancer.num_pieces) + ", " + str(len(dancer.pieces))
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
						#print dancer.first_name + " " + dancer.last_name + " is leaving " + leavingPiece.choreographer_name

						# rejected piece has to propose????


					"""
					# check if dancer is at capacity, in which case they will 
					# leave a dance 
					if len(dancer.pieces) < dancer.capacity:
						dancer.pieces[piece.piece_id] = pieceRank
					else:
						# dancer has to leave a piece
						worstID, worstPiece = findWorstPiece(dancer)
						leaveFromPiece(pieces[worstID],dancer)
						#todo: actually write this function LOL"""

				"""else: 
					# put dancer on alternates
					piece.alternates[dancerID] = piece.dancer_rankings[dancerID]""" 

				# remove curr dancer from proposal list
				piece.dancer_rankings.pop(dancerID)

	writePieces(pieces)
	makeAssigned(pieces)
	makeUnassigned(dancers)

main()

def test():
	pieces = csvToPieces(args.choreographer_prefs)
	dancers = csvToDancers(args.dancer_prefs, args.sign_in)

	print dancers[3]
	print "Dancer piece rankings (piece, rank): " + str(dancers[3].piece_rankings)
	print "Pieces dancer rankings (dancer #: rank): " + str(pieces[1].dancer_rankings)

	if not checkIfPieceRankedDancer(pieces[1], dancers[3]):
		print "good"
	if checkIfPieceRankedDancer(pieces[3], dancers[3]):
		print "yes"

#test()

