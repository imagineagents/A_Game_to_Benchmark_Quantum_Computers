# tools from quantum awesomeness directory
from devices import *# info on supported devices
try:
    import mwmatching as mw # perfect matching
except:
    pass

# other tools
import random, numpy, math, time, copy, os
from IPython.display import clear_output
import networkx as nx
import matplotlib.pyplot as plt
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# import the required SDKs
try:
    from qiskit import QuantumProgram
    import Qconfig
except:
    pass

try:
    from pyquil.quil import Program
    import pyquil.api as api
    from pyquil.gates import I, H, CNOT, CZ, RX, RY
except:
    pass

try:
    import projectq
    from projectq.ops import H, Measure, CNOT, C, Z, Rx, Ry
except:
    pass


def initializeQuantumProgram ( device, sim ):
    
    # *This function contains SDK specific code.*
    # 
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # * *sim* - Whether this is a simulated run
    # Process:
    # * Initializes everything required by the SDK for the quantum program. The details depend on which SDK is used.
    # Output:
    # * *q* - Register of qubits (needed by both QISKit and ProjectQ).
    # * *c* - Register of classical bits (needed by QISKit only).
    # * *engine* - Class required to create programs in QISKit, ProjectQ and Forest.
    # * *script* - The quantum program, needed by QISKit and Forest.

    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    if sdk in ["QISKit","ManualQISKit"]:
        engine = QuantumProgram()
        engine.set_api(Qconfig.APItoken, Qconfig.config["url"]) # set the APIToken and API url
        q = engine.create_quantum_register("q", num)
        c = engine.create_classical_register("c", num)
        script = engine.create_circuit("script", [q], [c]) 
    elif sdk=="ProjectQ":
        engine = projectq.MainEngine()
        q = engine.allocate_qureg( num )
        c = None
        script = None
    elif sdk=="Forest":
        if sim:
            engine = api.QVMConnection(use_queue=True)
        else:
            engine = api.QPUConnection(device)   
        script = Program()
        q = range(num)
        c = range(num)
        
    return q, c, engine, script


def implementGate (device, gate, qubit, script, frac = 0 ):
    
    # *This function contains SDK specific code.*
    # 
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # * *gate* - String that specifies gate type.
    # * *qubit* - Qubit, list of two qubits or qubit register on which the gate is applied.
    # * *script* - 
    # * *frac* -  
    # 
    # Process:
    # * For gates of type 'X', 'Z' and 'XX', the gate $U = \exp(-i \,\times\, gate \,\times\, frac )$ is implemented on the qubit or pair of qubits in *qubit*.
    # * *gate='Finish'* implements the measurement command on the qubit register required for ProjectQ to not complain.
    # 
    # Output:
    # * None are returned, but modifications are made to the classes that contain the quantum program.
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    if sdk in ["QISKit","ManualQISKit"]:
        if gate=='X':
            script.u3(frac * math.pi, -math.pi/2,math.pi/2, qubit )
        elif gate=='Z': # actually a Y axis rotation
            script.u3(frac * math.pi, 0,0, qubit )
        elif gate=='XX':
            if entangleType=='CX':
                script.cx( qubit[0], qubit[1] )
                script.u3(frac * math.pi, -math.pi/2,math.pi/2, qubit[0] )
                script.cx( qubit[0], qubit[1] )
            elif entangleType=='CZ':
                script.h( qubit[1] )
                script.cz( qubit[0], qubit[1] )
                script.u3(frac * math.pi, -math.pi/2,math.pi/2, qubit[0] )
                script.cz( qubit[0], qubit[1] )
                script.h( qubit[1] )
            else:
                print("Support for this is yet to be added")
    
    elif sdk=="ProjectQ":
        if gate=='X':
            Rx( frac * math.pi ) | qubit
        elif gate=='Z': # actually a Y axis rotation
            Ry( frac * math.pi ) | qubit
        elif gate=='XX':
            if entangleType=='CX':
                CNOT | ( qubit[0], qubit[1] )
                Rx( frac * math.pi ) | qubit[0]
                CNOT | ( qubit[0], qubit[1] )
            elif entangleType=='CZ':
                H | qubit[1]
                C(Z) | ( qubit[0], qubit[1] )
                Rx( frac * math.pi ) | qubit[0]
                C(Z) | ( qubit[0], qubit[1] )
                H | qubit[1]
            else:
                print("Support for this is yet to be added")
        elif gate=='finish':
            Measure | qubit
            
    elif sdk=="Forest":
        if gate=='X':
            if qubit in pos.keys(): # only if qubit is active
                script.inst( RX ( frac * math.pi, qubit ) )
        elif gate=='Z': # actually a Y axis rotation
            if qubit in pos.keys(): # only if qubit is active
                script.inst( RY ( frac * math.pi, qubit ) )
        elif gate=='XX':
            if entangleType=='CX':
                script.inst( CNOT( qubit[0], qubit[1] ) )
                script.inst( RX ( frac * math.pi, qubit[0] ) )
                script.inst( CNOT( qubit[0], qubit[1] ) )
            elif entangleType=='CZ':
                script.inst( H (qubit[1]) )
                script.inst( CZ( qubit[0], qubit[1] ) )
                script.inst( RX ( frac * math.pi, qubit[0] ) )
                script.inst( CZ( qubit[0], qubit[1] ) )
                script.inst( H (qubit[1]) )
            elif entangleType=='none':
                script.inst( RX ( frac * math.pi, qubit[0] ) )
                script.inst( RX ( frac * math.pi, qubit[1] ) )
            else:
                print("Support for this is yet to be added")

def getResults ( device, sim, shots, q, c, engine, script ):
    
    # *This function contains SDK specific code.*
    # 
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # 
    # Process:
    # * Implements all unitary quantum operations used in the program.
    # 
    # Output:
    # * None are returned, but modifications are made to the classes that contain the quantum program.
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    if sdk=="QISKit":
        # pick the right backend
        if sim:
            backend = 'local_qasm_simulator'
        else:
            backend = device
        # add measurement for all qubits
        for n in range(num):
            script.measure( q[n], c[n] )
           
        # execute job
        noResults = True
        while noResults:
            try: # try to run, and wait if it fails
                executedJob = engine.execute(["script"], backend=backend, shots=shots, max_credits = 5, wait=30, timeout=600)
                # get results
                resultsVeryRaw = executedJob.get_counts("script")
                if ('status' not in resultsVeryRaw.keys()): # see if it actually is data, and wai for 5 mins if not
                    noResults = False
                else:
                    print(resultsVeryRaw)
                    print("This is not data, so we'll wait and try again")
                    time.sleep(300)
            except:
                print("Job failed. We'll wait and try again")
                time.sleep(600)
                
        # invert order of the bit string and turn into probs
        resultsRaw = {}
        for string in resultsVeryRaw.keys():
            invertedString = string[::-1]
            resultsRaw[ invertedString ] = resultsVeryRaw[string]/shots
            
    elif sdk=="ManualQISKit":
        # add measurement for all qubits
        for n in range(num):
            script.measure( q[n], c[n] )
        qasm = engine.get_qasm("script")
        input("\nYou'll now be given the QASM representation of the circuit. Find a way to run it, and then copy the results in the input box...\n")
        input("The results you provide should be in the form of a dictionary, with bit strings as keys and the fraction of times these occurred as a result as values...")
        input("Well, actually you should find some way to do this programatically. The function 'getResults' is what you need to look at. But copy and paste will do for now....\n")
        resultsRaw = eval(input(qasm+"\n"))
    
    elif sdk=="ProjectQ":
        engine.flush()
        # list of bit strings
        strings = [''.join(x) for x in product('01', repeat=num)]
        # get prob for each bit string to make resultsRaw
        resultsRaw = {}
        for string in strings:
            resultsRaw[ string ] = engine.backend.get_probability( string, q )
            
    elif sdk=="Forest":
        
        # get list of active (and therefore plotted) qubits
        qubits_active = list(pos.keys())

        # execute job
        noResults = True
        while noResults:
            try: # try to run, and wait for 10 mins if it fails
                resultsVeryRaw = engine.run_and_measure(script, qubits_active, trials=shots)
                noResults = False
            except:
                print("Job failed. We'll wait and try again.")
                time.sleep(1800)
                
        # convert them the correct form
        resultsRaw = {}
        for sample in resultsVeryRaw:
            bitString = ""
            disabled_so_far = 0
            for qubit in range(num):
                if qubit in qubits_active:
                    bitString += str(sample[qubit-disabled_so_far])
                else:
                    bitString += "0" # fake result for dead qubit
                    disabled_so_far += 1
            if bitString not in resultsRaw.keys():
                resultsRaw[bitString] = 0
            resultsRaw[bitString] += 1/shots 
    
    return resultsRaw


def printM ( string, move ):
    
    # If *move=M*, this is just *print()*. Otherwise it does nothing.

    if move=="M":
        print(string)


def entangle( device, move, shots, sim, gates, conjugates ):
    
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # * *move* -
    # * *shots* -
    # * *sim* -
    # * *gates* - Entangling gates applied so far. Each round of the game corresponds to two 'slices'. *gates* is a list with a dictionary for each slice. The dictionary has pairs of qubits as keys and fractions of pi defining a corresponding entangling gate as values.
    # * *conjugates* - List of single qubit gates to conjugate entangling gates of previous rounds. Each is specified by a two element list. First is a string specifying the rotation axis ('X' or 'Z'), and the second specifies the fraction of pi for the rotation.
    #
    # Process:
    # * Sets up and runs a quantum circuit consisting of all gates thus far.
    #
    # Output:
    # * *oneProb* - A list with an entry for each qubit. Each entry is the fraction of samples for which the measurement of that qubit returns *1*.
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    q, c, engine, script = initializeQuantumProgram(device,sim)

    # apply all gates
    # gates has two entries for each round, except for the current round which has only one
    rounds = int( (len(gates)+1)/2 )
    
    # loop over past rounds and apply the required gates
    for r in range(rounds-1):

        # do the first part of conjugation (the inverse)
        for n in range(num):
            implementGate ( device, conjugates[r][n][0], q[n], script, frac=-conjugates[r][n][1] )

        # get the sets of gates that create and (attempt to) remove the puzzle for this round
        gates_create = gates[2*r]
        gates_remove = gates[2*r+1]
        
        # determine which pairs are for both, and which are unique
        pairs_both = list( set(gates_create.keys()) & set(gates_remove.keys()) )
        pairs_create = list( set(gates_create.keys()) - set(gates_remove.keys()) )
        pairs_remove = list( set(gates_remove.keys()) - set(gates_create.keys()) )
              
        # then do the exp[ i XX * frac ] gates accordingly
        for p in pairs_both:
            #print([r,p,gates_create[p]+gates_remove[p]] )
            implementGate ( device, "XX", [ q[pairs[p][0]], q[pairs[p][1]] ], script, frac=(gates_create[p]+gates_remove[p]) )
        for p in pairs_create:
            #print([r,p,gates_create[p]] )
            implementGate ( device, "XX", [ q[pairs[p][0]], q[pairs[p][1]] ], script, frac=(gates_create[p]) )
        for p in pairs_remove:
            #print([r,p,gates_remove[p]] )
            implementGate ( device, "XX", [ q[pairs[p][0]], q[pairs[p][1]] ], script, frac=(gates_remove[p]) )
            
        # do the second part of conjugation
        for n in range(num):
            implementGate ( device, conjugates[r][n][0], q[n], script, frac=conjugates[r][n][1] )
    
    # then the same for the current round (only needs the exp[ i XX * (frac - frac_inverse) ] )
    r = rounds-1
    for p in gates[2*r].keys():
        implementGate ( device, "XX", [ q[ pairs[p][0] ], q[ pairs[p][1] ] ], script, frac=gates[2*r][p] )
    
    
    resultsRaw = getResults( device, sim, shots, q, c, engine, script )
    
    strings = list(resultsRaw.keys())
    
    if sim==True:
        # sample from this prob dist shots times to get results
        results = {}
        for string in strings:
            results[string] = 0
        for shot in range(shots):
            j = numpy.random.choice( len(strings), p=list(resultsRaw.values()) )
            results[strings[j]] += 1/shots
    else:
        results = resultsRaw
        
    # determine the fraction of results that came out as 1 (instead of 0) for each qubit
    oneProb = [0]*num
    for bitString in strings:
        for v in range(num):
            if (bitString[v]=="1"):
                oneProb[v] += results[bitString]
    
    implementGate ( device, "finish", q, script )
    
    return oneProb


def calculateEntanglement( oneProb ):
    
    # was once the mixedness
    # E = 1-2*abs( 0.5-oneProb )
    #but now based on frac
    
    E = ( 2 * calculateFrac( oneProb ) )    
    return min( E, 1)

def calculateFrac ( oneProb ):

    # Prob(1) = sin(frac*pi/2)^2
    # therefore frac = asin(sqrt(oneProb)) *2 /pi
    frac = math.asin(math.sqrt( oneProb )) * 2 / math.pi
    
    return frac
    

def calculateFuzz ( oneProb, pairs, matchingPairs ):
    
    # Input:
    # * *oneProb* - A list with an entry for each qubit.
    #               Each entry is the fraction of samples for which the measurement of that qubit returns *1*.
    # * *matchingPairs* - The pairing of qubits in the current round.
    # 
    # Process:
    # * The two qubits of the same pair should have the same oneProb value. If they don't, it is because of fuzz.
    #   The fuzz is therefore quantified by the average difference between these values.
    # 
    # Output:
    # * *fuzzAv* - As described above.
    
    fuzzAv = 0
    for p in matchingPairs:
        fuzzAv += abs( oneProb[pairs[p][0]] - oneProb[pairs[p][1]] )/len(matchingPairs)
 
    return fuzzAv


def printPuzzle ( device, oneProb, move ):
    
    # ### *printPuzzle*
    # 
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # * *oneProb* - A list with an entry for each qubit.
    #               Each entry is the fraction of samples for which the measurement of that qubit returns *1*.
    #
    # Process:
    # * The contents of *oneProb* contains some basic clues about the circuit that has been performed. It is the player's job to use those clues to guess the circuit. This means we have to print *oneProb* to screen. In order to make the game a pleasant experience and help build intuition about the device, this is done visually. The networkx package is used to visualize the layout of the qubits, and the oneProb information is conveyed using colour. 
    # 
    # Output:
    # * None returned, but the above described image is printed to screen.
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    if move=="M":
        
        # create a graph with qubits as vertices and possible entangling gates as edges

        G=nx.Graph()

        for p in pairs:
            if p[0:4]!='fake':
                G.add_edge(pairs[p][0],pairs[p][1])

        for p in pairs:
            if p[0:4]!='fake':
                G.add_edge(pairs[p][0],p)
                G.add_edge(pairs[p][1],p)
                pos[p] = [(pos[pairs[p][0]][dim] + pos[pairs[p][1]][dim])/2 for dim in range(2)]

        # colour and label the edges with the oneProb data
        colors = []
        sizes = []
        labels = {}
        for node in G:
            if type(node)!=str:
                if (oneProb[node]>1): # if oneProb is out of bounds (due to this node having already been selected) make it grey
                    colors.append( (0.5,0.5,0.5) )
                else: # otherwise it is on the spectrum between red and blue
                    # E = min(1, 2*calculateFrac( oneProb[node] ) ) # colour is determine by the guessed frac
                    E = calculateEntanglement( oneProb[node] ) # colour is determined by entanglement
                    colors.append( (E,0,1-E) )
                sizes.append( 3000 )
                if oneProb[node]>1:
                    labels[node] = ""
                elif oneProb[node]==0.5:
                    labels[node] = "99"
                else:
                    labels[node] = "%.0f" % ( 100 * ( E ) )
            else:
                colors.append( "black" )
                sizes.append( 1000 )
                labels[node] = node

        # show it

        plt.figure(2,figsize=(2*area[0],1.25*area[1])) 
        nx.draw(G, pos, node_color = colors, node_size = sizes, labels = labels, with_labels = True,
                font_color ='w', font_size = 22.5)

        plt.show()

        
def calculateFracDifference (frac1, frac2):
    
    delta = max(frac1,frac2) - min(frac1,frac2)
    delta = min( delta, 1-delta )
    return delta  
        

def getDisjointPairs ( pairs, oneProb = [] ):

    # Input:
    # * *pairs* - A dictionary with names of pairs as keys and lists of the two qubits of each pair as values
    # 
    # Process:
    # * A graph is created using the pairs as edges, and is assigned random weights.
    #   These max weight matched to find a disjoint set of pairs.
    # 
    # Output:
    # * *matchingPairs* - A list of the names of a random set of disjoint pairs included in the matching.
    
    # if a set of oneProbs is supplied, the weight for an edge is the difference between their fracs
    weight = {}
    for p in pairs.keys():
        if oneProb:
            weight[p] = -calculateFracDifference( calculateFrac( oneProb[ pairs[p][0] ] ) , calculateFrac( oneProb[ pairs[p][1] ] ) )
        else:
            weight[p] = random.randint(0,100)     
    
    edges = []
    for p in pairs.keys():
        edges.append( ( pairs[p][0], pairs[p][1], weight[p] ) )
    
    # match[j] = k means that edge j and k are matched
    match = mw.maxWeightMatching(edges, maxcardinality=True)
    
    # get a list of the pair names for each pair in the matching (not including fakes)
    matchingPairs = []
    for v in range(len(match)):
        for p in pairs.keys():
            if pairs[p]==[v,match[v]] and p[0:4]!='fake' :
                matchingPairs.append(p)
                
    return matchingPairs


def runGame ( device, move, shots, sim, maxScore, dataNeeded=True, clean=False, game=-1):
    
    # Input:
    # * *device* - String specifying the device on which the game is played.
    #              Details about the device will be obtained using getLayout.
    # * *move* -
    # * *shots* -
    # * *sim* -
    #
    # Process:
    # * Run the game!
    #
    # Output:
    # * *score* - score reached by the player at game over
    # * *gates*
    # * *conjugates*
    # * *totalFuzz* - the fuzz for each level (see calculateFuzz)
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    gates = []
    conjugates = []
    totalFuzz = []
    oneProbs = []
    
    # if we are running off data, load up oneProbs for a move='C' run and see what the right answers are
    if dataNeeded==False:
        # oneProbs
        filename = 'move=C_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
        saveFile = open('results_' + device + '/oneProbs_'+filename)
        oneProbSamples = saveFile.readlines()
        saveFile.close()
        # gates
        filename = 'move=C_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
        saveFile = open('results_' + device + '/gates_'+filename)
        gateSamples = saveFile.readlines()
        saveFile.close()
        
        samples = len(oneProbSamples) # find out how many samples there are
        
        if maxScore==0: # if a maxScore is not given, use the value from the first sample
            maxScore = len( eval( oneProbSamples[ 0 ] ) )
        
        # choose a game randomly, if a specific one was not requested
        if game==-1:
            game = random.randint( 0, samples-1 )
        # get the data for this game
        oneProbs = eval( oneProbSamples[ game ] )
        originalOneProbs = copy.deepcopy( oneProbs )
        gates = eval( gateSamples[ game ] )

            
            
    
    gameOn = True
    restart = False
    score = 0
    while gameOn:
        
        score += 1
        
        # Step 1: get a new puzzle
        
        if dataNeeded:
          
            # if running anew, we generate a new set of gates
  
            # gates applied are of the form
            # CNOT | (j,k)
            # Rx(frac*pi) | j
            # CNOT | (j,k)
            # and so are specified by a pair p=[j,k] and a random fraction frac
  
            # first we generate a random set of edges
            matchingPairs = getDisjointPairs( pairs )
          
            # then we add gates these to the list of gates
            appliedGates = {}
            for p in matchingPairs:
                frac = random.random() / 2 # this will correspond to a 0 \leq frac*pi \leq pi/2 rotation 
                appliedGates[p] = frac
            gates.append(appliedGates)
          
            # all gates so far are then run
            oneProb = entangle( device, move, shots, sim, gates, conjugates)
          
        else:
            
            oneProb = oneProbs[score-1]
            matchingPairs = list(gates[ 2*(score-1) ].keys())
            
            #rawOneProb = copy.copy( oneProb )
            #onepProb = CleanData([0.9738415386108479, 0.17136714125145475, 0.6570613910686468, -0.4049062006204463, 0.8279469669214491, 0.06886165802725541, 0.5259991338702945, 0.1705404978526586, 1.1073117445006242, -0.1495970624698746, 0.8924091185860883, 0.01464239225931483, 1.0275477884441937, 0.17756205518906018, 0.9049031949729898, 0.280396190827653, 1.2514180812275613, -0.11943897690379385, 0.8361128832390184, 0.2723795879551341, 1.0740835372348418, 0.18770411873513015, 1.0433061367657521, 0.08620002219277448, 1.0700458928035512, 0.036695062474293084, 1.358823265090365, 0.2344385515227468, 1.0781565176136898, 0.1215383109298111, 1.1196610768179336, -0.02413677657431527, 0.5486294115960706, -0.08863255029559444, 0.8011715218602745, -0.1561339422399854, 0.9524787659612552, -0.22868678766470124, 1.018739461233587, -0.13198786838761742],oneProb) 
        
        
        # Step 2: Get player to guess pairs
        
        displayedOneProb = copy.copy( oneProb )
        
        guessedPairs = []

        # if choices are all correct, we just give the player the right answer
        if (move=="C"):
            guessedPairs = matchingPairs
        # if choices are random, we generate a set of random pairs
        if (move=="R"):
            guessedPairs = getDisjointPairs( pairs )
        # if choices are via MWPM, we do this
        if (move=="B"):
            guessedPairs = getDisjointPairs( pairs, oneProb=oneProb )
        # if choices are manual, let's get choosing
        if (move=="M"):
            
            # get the player choosing until the choosing is done
            unpaired = num
            restart = False
            while (unpaired>1):  
                
                clear_output()
                print("")
                print("Round "+str(score))
                printPuzzle( device, displayedOneProb, move )
                
                pairGuess = input("\nChoose a pair  (or type 'done' to skip to the next round, or 'restart' for a new game)\n")
                if num<=26 : # if there are few enough qubits, we don't need to be case sensitive
                    pairGuess = str.upper(pairGuess)

                if (pairGuess in pairs.keys()) and (pairGuess not in guessedPairs) :

                    guessedPairs.append(pairGuess)

                    # set them both to grey on screen (set the corresponding oneProb value to >1)
                    for j in [0,1]:
                        displayedOneProb[ pairs[pairGuess][j] ] = 2
                    printM("\n\n\n", move)
                    
                    # check if all active (and therefore displayed) vertices have been covered
                    unpaired = 0
                    for n in pos.keys():
                        unpaired += ( displayedOneProb[n] <= 1 )
                
                elif (str.upper(pairGuess)=="DONE") : # player has decided to stop pairing
                    unpaired = 0
                elif (str.upper(pairGuess)=="RESTART") : # player has decided to stop the game
                    unpaired = 0
                    restart = True
                else:
                    printM("That isn't a valid pair. Try again.\n(Note that input can be case sensitive)", move)
        
        
        # get the fuzz for this level
        totalFuzz.append( calculateFuzz( oneProb, pairs, matchingPairs ) )  
        # store the oneProb
        oneProbs.append( oneProb )
        
        # see whether the game over condition is satisfied
        gameOn = (score<maxScore) and restart==False
        
        # given the chosen pairs, the gates are now deduced from oneProb
        guessedGates = {}

        for p in guessedPairs:

            guessedOneProb = 0
            for j in range(2):
                guessedOneProb += oneProb[ pairs[p][j] ] / 2
            
            guessedFrac = calculateFrac( guessedOneProb )
            
            # since the player wishes to apply the inverse gate, the opposite frac is stored
            guessedGates[p] = -guessedFrac

        # now we can add to the list of all gates
        gates.append(guessedGates)
        
        # finally randomly generate X or Z rotation for each active qubit to conjugate this round with
        newconjugates = []
        for n in range(num):
            newconjugates.append( [ numpy.random.choice(['X','Z']) , random.random() ] )
        conjugates.append(newconjugates)
             
        clear_output()
        #printPuzzle( device, rawOneProb, move )
        printPuzzle( device, oneProb, move )
        printM("", move)
        printM("Round "+str(score)+" complete", move)
        printM("", move)
        printM("Pairs you guessed for this round", move)
        printM(sorted(guessedPairs), move)
        printM("Pairs our bot would have guessed", move)
        printM(sorted(getDisjointPairs( pairs, oneProb=oneProb )), move)
        printM("Correct pairs for this round", move)
        printM(sorted(matchingPairs), move)
        correctGuesses = list( set(guessedPairs).intersection( set(matchingPairs) ) )
        printM("\nYou guessed "+str(len(correctGuesses))+" out of "+str(len(matchingPairs))+" pairs correctly!", move)
        printM("", move)
        printM("", move)
        if move=="M" and restart==False:
            input(">Press Enter for the next round...\n")
            print(" The next round is being prepared\n")
    
    if move=="M" and restart==False:
        input("> There is no more data on this game :( Press Enter to restart...\n")
    
    return gates, conjugates, totalFuzz, oneProbs



def MakeGraph(X,Y,y,axisLabel,labels=[],verbose=False,log=False):
    
    plt.rcParams.update({'font.size': 30})
    
    # convert the variances of varY into widths of error bars
    for j in range(len(y)):
        for k in range(len(y[j])):
            y[j][k] = math.sqrt(y[j][k]/2)
    
    plt.figure(figsize=(20,10))
    
    # add in the series
    for j in range(len(Y)):
        if labels==[]:
            plt.errorbar(X, Y[j], marker = "x", markersize=20, yerr = y[j], linewidth=5)
        else:
            plt.errorbar(X, Y[j], label=labels[j], marker = "x", markersize=20, yerr = y[j], linewidth=5)
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    
    # label the axes
    plt.xlabel(axisLabel[0])
    plt.ylabel(axisLabel[1])
    
    # make sure X axis is fully labelled
    plt.xticks(X)

    # logarithms if required
    if log==True:
        plt.yscale('log')

    # make the graph
    plt.show()
    
    plt.rcParams.update(plt.rcParamsDefault)
    
    # if verbose, print the numbers to screen
    if verbose==True:
        print("\nX values")
        print(X)
        for j in range(len(Y)):
            print("\nY values for series "+str(j))
            print(Y[j])
            print("\nError bars")
            print(y[j])
            print("")


def GetData ( device, move, shots, sim, samples, maxScore ):

    for sample in range(samples):

        print("move="+move+", shots="+str(shots)+", sample=" + str(sample+1) )

        gates, conjugates, totalFuzz, oneProbs = runGame( device, move, shots, sim, maxScore )

        # make a directory for this device if it doesn't already exist
        if not os.path.exists('results_' + device):
            os.makedirs('results_' + device)

        filename = 'move=' + move + '_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'

        saveFile = open('results_' + device + '/totalFuzz_'+filename, 'a')
        saveFile.write( str(totalFuzz)+'\n' )
        saveFile.close()

        saveFile = open('results_' + device + '/oneProbs_'+filename, 'a')
        saveFile.write( str(oneProbs)+'\n' )
        saveFile.close()

        saveFile = open('results_' + device + '/gates_'+filename, 'a')
        saveFile.write( str(gates)+'\n' )
        saveFile.close()

        saveFile = open('results_' + device + '/conjugates_'+filename, 'a')
        saveFile.write( str(conjugates)+'\n' )
        saveFile.close()
        
        
def CalculateQuality ( x, oneProbSamples, gateSamples, pairs, score, type='both') :
    
    # see what fraction of the matchings we have corrent
    
    fractionCorrect = 0
    closenessToIdeal = 0
    for oneProbs, gates in zip(oneProbSamples, gateSamples):
        
        oneProb = eval(oneProbs)[score-1]
        
        if x!=[]:
            oneProb = CleanData ( x, oneProb )

        gate = eval(gates)[ 2*(score-1) ]
        
        matchingPairs = list(gate.keys())
        guessedPairs = getDisjointPairs( pairs, oneProb=oneProb )
        correctGuesses = list( set(guessedPairs).intersection( set(matchingPairs) ) )
        fractionCorrect += len(correctGuesses) / len(matchingPairs)
            
        realFracs = [0]*len(oneProb)
        for p in gate.keys():
            realFracs[pairs[p][0]] = gate[p]
            realFracs[pairs[p][1]] = gate[p]
        for prob,realFrac in zip(oneProb,realFracs):
            closenessToIdeal += (calculateFrac(prob)-realFrac)**2 / len(oneProb)
            
    
    fractionCorrect = fractionCorrect / len( oneProbSamples )
    closenessToIdeal = 1-math.sqrt( closenessToIdeal / len( oneProbSamples ) )
            
    return [fractionCorrect,closenessToIdeal]


def CleanData ( x, oneProb ):
     
    for n in range(len(oneProb)):
        oneProb[n] = x[2*n] * oneProb[n] + x[2*n+1]
        oneProb[n] = min(1,oneProb[n])
        oneProb[n] = max(0,oneProb[n])
    
    return oneProb


def Metropolis ( x, oneProbSamples, gateSamples, num, pairs, score, steps=1000, repetitions=10, delta=0.025, T=0.01 ):

    best_x = copy.deepcopy(x)
    bestQuality = CalculateQuality ( x, oneProbSamples, gateSamples, pairs, score )
    bestDiff = 0
        
    for rep in range(repetitions):
        
        print("\nrepetition = ", rep, "\nbest fraction = ", bestQuality[0], ", best closeness = ", bestQuality[1])
        
        x = copy.deepcopy(best_x)
        quality = copy.deepcopy(bestQuality)
        
        for step in range(steps):

            n = random.randint(0,2*num-1)
            random_delta = random.uniform(+delta,-delta)

            x[n] += random_delta

            proposedQuality = CalculateQuality ( x, oneProbSamples, gateSamples, pairs, score )

            diff = 1*(proposedQuality[0]-quality[0]) + 2*(proposedQuality[1]-quality[1])
            
            accept = ( random.random() < math.exp(diff/T) )

            if accept:
                quality = copy.deepcopy(proposedQuality)
            else:
                x[n] -= random_delta

            if (quality[0]>bestQuality[0]):
                bestDiff
                best_x = copy.deepcopy(x)
                bestQuality = copy.deepcopy(quality)
                print("\nstep = ",step,"\nbest fraction = ", bestQuality[0], ", best closeness = ", bestQuality[1], "\nbest x = ", best_x)
            
    return best_x


def CreateCleaningProfile ( device, move, shots, sim ) :
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    # oneProbs
    filename = 'move=' + move + '_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
    saveFile = open('results_' + device + '/oneProbs_'+filename)
    oneProbSamples = saveFile.readlines()
    saveFile.close()
    # gates
    filename = 'move=' + move + '_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
    saveFile = open('results_' + device + '/gates_'+filename)
    gateSamples = saveFile.readlines()
    saveFile.close()
        
    maxScore = len( eval(oneProbSamples[0]) )
    
    cleaner = []
    for score in range(1,maxScore+1):
        x = [1,0]*num
        print("score = ",score)
        cleaner.append( Metropolis ( x, oneProbSamples, gateSamples, num, pairs, score ) )
     
    filename = 'move=' + move + '_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
    saveFile = open('results_' + device + '/cleaner_'+filename, 'a')
    saveFile.write( str(cleaner)+'\n' )
    saveFile.close()


def ProcessData ( device, move, shots, sim ):
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout(device)
    
    filename = 'move=' + move + '_shots=' + str(shots) + '_sim=' + str(sim) + '.txt'
    
    # get fuzz data
    saveFile = open('results_' + device + '/totalFuzz_'+filename)
    fuzzSamples = saveFile.readlines()
    saveFile.close()
    
    # get oneprob data
    saveFile = open('results_' + device + '/oneProbs_'+filename)
    oneProbSamples = saveFile.readlines()
    saveFile.close()
    
    # for each round, get mean of all Es
    # note, variable names make it sound like we are averaging oneProb, but we aren't: hacky mess :(
    meanOneProbSamples = []
    for sample in oneProbSamples:
        sample = eval(sample)
        meanOneProbs = []
        for roundOneProbs in sample:
            mean = 0
            for oneProb in roundOneProbs:
                mean += calculateEntanglement(oneProb)/num
            meanOneProbs.append( mean )
        meanOneProbSamples.append( meanOneProbs )
    
    # find number of samples
    samples = len(fuzzSamples)
    
    # note: from here on, score means something that starts at 0, rather than starting at 1 as it does elsewhere
    
    # find number of round in samples (assume same for all)
    maxScore = len(eval(fuzzSamples[0]))
    
    fuzzAv = [[0]*maxScore for _ in range(2)]
    for totalFuzz in fuzzSamples:
        totalFuzz = eval(totalFuzz)
        for score in range(maxScore):
            fuzzAv[0][score] += totalFuzz[score]/samples
            fuzzAv[1][score] += totalFuzz[score]**2/samples
    for score in range(maxScore):
        fuzzAv[1][score] -= fuzzAv[0][score]**2
        
    entangleAv = [[0]*maxScore for _ in range(2)]
    for meanOneProbs in meanOneProbSamples:
        for score in range(maxScore):
            entangleAv[0][score] += meanOneProbs[score]/samples
            entangleAv[1][score] += meanOneProbs[score]**2/samples
    for score in range(maxScore):
        entangleAv[1][score] -= entangleAv[0][score]**2
        
    # get gate data
    saveFile = open('results_' + device + '/gates_'+filename)
    gateSamples = saveFile.readlines()
    saveFile.close() 
        
    quality = []
    for score in range(maxScore):
        quality.append( CalculateQuality ( [], oneProbSamples, gateSamples, pairs, score+1 ) )
        
    return fuzzAv, entangleAv, quality


def PlayGame():
    
    clear_output()
    print("")
    print("")
    print("            __   _  _   __   __ _  ____  _  _  _  _               ")          
    print("           /  \\ / )( \\ / _\\ (  ( \\(_  _)/ )( \\( \\/ )              ")          
    print("          (  O )) \\/ (/    \\/    /  )(  ) \\/ (/ \\/ \\              ")          
    print("           \\__\\)\\____/\\_/\\_/\\_)__) (__) \\____/\\_)(_/              ")         
    print("  __   _  _  ____  ____   __   _  _  ____  __ _  ____  ____  ____ ") 
    print(" / _\\ / )( \\(  __)/ ___) /  \\ ( \\/ )(  __)(  ( \\(  __)/ ___)/ ___)") 
    print("/    \\\\ /\\ / ) _) \\___ \\(  O )/ \\/ \\ ) _) /    / ) _) \\___ \\\\___ \\") 
    print("\\_/\\_/(_/\\_)(____)(____/ \\__/ \\_)(_/(____)\\_)__)(____)(____/(____/") 
    print("")
    print("            A GAME TO BENCHMARK QUANTUM COMPUTERS")
    print("                     by James R. Wootton")
    print("                University of Basel/Decodoku")
    print("")
    print("")

    input("> Press Enter to continue...\n")
    
    intro = str.upper(input("\n> Do you want to read the introduction? (y/n)...\n"))
    if intro!="N":
        input("> There are lots of quantum processors around these days. But how good are they really?...\n")
        input("> How do they compare to each other, and how do they compare to normal computers?...\n")
        input("> To find out, we can run a simple program on them and see what happens...\n")
        input("> So that's what we've done. We made a game, and we are running it on all the quantum computers we can...\n")
              
        input("> Have a play, and see what you think...\n")
        input("> You won't learn anything about the mysteries of the quantum world by playing...\n")
        input("> But you will find out how good current quantum computers are at being computers...\n")
        input("> The larger and fancier a quantum processor is, the better the puzzles in the game will be...\n")
        input("> The noisier that a quantum processor is, the more infuriatingly steep the difficulty curve will be...\n")
        input("> So the quality of the processor is direcly proportional to how much fun you have playing on it...\n")
        input("> Now choose a device to test out...\n")
    deviceNotChosen = True
    attempt = 0
    deviceList = ""
    for device in supportedDevices():
        deviceList += device + " "
    while deviceNotChosen:
        message = "> The devices you can play on are\n\n  " + deviceList + "\n\n> Type the one you'd like below...\n"
        message = "\n> I'm afraid I didn't understand that.\n"*(attempt>0) + message
        device = input(message)
        if device in supportedDevices():
            deviceNotChosen = False
        else:
            attempt += 1
    
    num, area, entangleType, pairs, pos, example, sdk, runs = getLayout( device )
    
    num_active_qubits = len(pos.keys())
    
    tut = str.upper(input("\n> Do you want to read the tutorial? (y/n)...\n"))
    if tut!="N":
        printPuzzle(device,example,"M")
        input("> The game is a series of puzzles, which look something like this...\n")
        input("> All the coloured circles" + ((num_active_qubits%2)==1)*" (except one)" + " are paired up...\n")
        input("> Your job is to identify these pairs...\n")
        input("> You do this by looking at the numbers: Circles should have very similar numbers if they are paired...\n")
        input("> As you proceed through the game, the two numbers in each pair will get less similar. This will make the puzzles harder...\n")
        input("> The game is designed to have a nice gentle increase in difficulty...\n")
        input("> But noise in the quantum processors increases the difficulty much faster...\n")
        input("> If you want to see how potent noise is, compare a run on the real device with one on a (noiseless) simulator...\n")
        input("> You can play some games on the simulator to see how things should be...\n")
        input("> Or you can play using data from the real device...\n")  
        
            
    s = str.upper(input("> Do you want to play a game using data from the real device? (y/n)...\n"))
    sim = (s!='Y')
    if sim:
        input("> The following game data will be from a simulated run...\n")
    
    shots = min( runs[sim]['shots'] )
    runGame ( device, 'M', shots, sim, 0, dataNeeded=False )
    try:
        runGame ( device, 'M', shots, sim, 0, dataNeeded=False )
    except:
        input("> Something went wrong. This probably means there is no saved data to play the game you requested.\n> Try choosing a different device...\n")

