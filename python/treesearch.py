#! /usr/bin/env python
# This work is licensed under a Creative Commons Attribution-Noncommercial-
# Share Alike 3.0 United States License. See:
#     http://creativecommons.org/licenses/by-nc-sa/3.0/us/
# for details. My name and / or a link to www.danielcasner.org must be
# maintained if you use this module or create a derivative work which copies
# code substantially from this module.
#
# Questions regarding comertial use of the software should be directed to the
# author at daniel@danielcasner.org
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. 
__doc__ = """
This module provides higher order functions for basic tree search and A*
(A-star) and A*-beam search algorithms as particular examples. The basic data
structure is a Node (see below), successor functions operate on Nodes and the
solution if found will be a Node.

Familiarity with tree search and A* is assumed. For good background see Norvig's
"Artificial Intelligence: A Modern Approach." While traditional implementations
are generally recursive, this implementation has been optimized for Python using
loops and list comprehensions.
"""
__author__ = "Daniel Casner <www.danielcasner.org/code>"
__version__ = "2.2.1"


class Node(object):
    """
The basic data structure for tree search. Contains the state, search depth, cost
to reach the state, the action taken to reach the state from the parent node's
state and a reference to the parent.
While this is basically a recursive data structure, iteration is supported so
list comprehensions can be used on Nodes. E.g.:
    actions = [n.action for n in solution]
or
    path = [n.state for n in solution]
"""
    def __init__(self, state, cost=0, action=None, parent=None, depth=None):
        self.state  = state
        self.cost   = cost
        self.action = action
        self.parent = parent
        if depth is None:
            if parent: self.depth = parent.depth + 1
            else: self.depth = 0
    def __str__(self):
        return "<Node: State=%s, Action=%s, Depth=%d, Cost=%f>" % \
               (self.state, self.action, self.depth, self.cost)
    def __iter__(self):
        n = self
        while n:
            yield n
            n = n.parent

def treeSearch(start, successorFtn, goalP, insert, eoqa, genSucP, heuristic):
    """A general higher order function for tree searches
start           The starting Node. Only the information requireed by
                successorFtn need be non None.
successorFtn    A callable which accepts a node and returns a list of possible
                successor nodes.
goalP           A predicate callable returning True if the Node is the goal.
insert          A callable which does inplace insertion of successors into the
                fringe (side effecting).
eoqa            Called when there are no more nodes on the fringe. I.e. we
                failed to find a solution.
genSucP         A predicate callable indicating returning True if a Node should
                be expanded, i.e. it's successors added to the fringe.
heuristic       Called by the insert function to generate search heuristics.

See Astar below for an example call pattern and auxillary functions.
"""
    # The list fringe stores the value of each leave along with its h(n) value
    # so that it doesn't have to be recalculated repeatedly.
    fringe = [(start, 0)]
    while fringe:
        node = fringe.pop(0)[0]
        if goalP(node):
            return node
        elif genSucP(node):
            insert(removeDups(successorFtn(node), node, fringe), fringe, heuristic)
    # Failed to find a solution
    return eoqa(fringe, successorFtn, goalP, insert, eoqa, genSucP, start)
        

def removeDups(successors, node, fringe):
    "Duplicate removal function for treeSearch, greatly improves speed."
    def isNew(state, lineage):
        return not state in [n.state for n in lineage]
    def isNotOnFringe(state, fringe):
        return not state in [f[0].state for f in fringe]
    # Yay for list comprehensions
    return [n for n in successors if isNew(n.state, node) and isNotOnFringe(n.state, fringe)]

################################################################################
#####                            A* Search                                 #####
################################################################################

def Astar(start, successorFtn, goalP, heuristic):
    """The connonical A* search algorithm.
start           The starting Node.
successorFtn    A callable which accepts a node and returns a list of possible
                successor nodes.
goalP           A predicate callable returning True if the Node is the goal.
heuristic       A callable which returns the heuristic (guessed) cost from a
                state to the goal state. Note, heuristic must be, admissable,
                i.e. estimate is always less than or equal to the true cost.
"""
    return treeSearch(start, successorFtn, goalP, AstarInsert, AstarEOQA, AstarGenSuc, heuristic)

def AstarInsert(successors, queue, h):
    """Insert function for Astar search.
This is really what makes A* search A*. successors, queue and h (heuristic) will
be passed in by treeSearch when calling. queue is updated in place.
"""
    def cost(n): return n[0].cost + n[1]
    def sortFtn(x, y): return cmp(cost(x), cost(y))
    pairs = [(s, h(s.state)) for s in successors]
    pairs.sort(sortFtn)
    i = 0
    while pairs and i < len(queue):
        if cost(queue[i]) < cost(pairs[0]): i += 1
        else: queue.insert(i, pairs.pop(0))
    queue.extend(pairs) # And add all the rest if any

def AstarEOQA(*args):
    "End of queue action for A* search"
    #print "A* search failed to find a solution"
    return None

def AstarGenSuc(node):
    """Generate successors predicate for A* search.
In basic A* search we always expand nodes regardless of depth.
"""
    return True

################################################################################
#####                          A* Beam Search                              #####
################################################################################

def AstarBeam(start, successorFtn, goalP, heuristic, beamLength=100):
    """A*-beam search using treeSearch.
This is identical to A* except that the fringe is not allowed to grow beyond a
specified length bounding memory consumption."""

    def AstarBeamInsert(successors, queue, h):
        "Insert function for A*-beam search."
        # Even though we will be truncating the result, we still need to caluculate the full insert
        AStarInsert(successors, queue, h)
        # Just truncate to the best beamLength elements of what ASstarInsert gives.
        queue = queue[:beamLength]
    
    return treeSeach(start, successorFtn, goalP, AstarBeamInsert, AstarEOQA,
                     AstarGenSuc, heuristic)


################################################################################
#####           Cannonical Traveling Sales-person Problem test             #####
################################################################################
# This uses a sample problem to test the A* search
if __name__ == '__main__':
    from time import time
    neighbors = {
        'Oradea': (('Zerind', 71), ('Sibiu', 151)),
        'Sibiu':  (('Rimnicu Vilcea', 80), ('Oradea', 151), ('Arad', 140), ('Fagaras', 99)),
        'Fagaras': (('Sibiu', 99), ('Bucharest', 211)),
        'Zerind': (('Oradea', 71), ('Arad', 75)),
        'Arad': (('Zerind', 75), ('Sibiu', 140), ('Timisoara', 118)),
        'Timisoara': (('Arad', 118), ('Lugoj', 111)),
        'Lugoj': (('Timisoara', 111), ('Mehadia', 70)),
        'Mehadia': (('Lugoj', 70), ('Dobreta', 75)),
        'Dobreta': (('Mehadia', 75), ('Craiova', 120)),
        'Craiova': (('Dobreta', 120), ('Rimnicu Vilcea', 146), ('Pitesti', 138)),
        'Rimnicu Vilcea': (('Craiova', 146), ('Sibiu', 80), ('Pitesti', 97)),
        'Pitesti': (('Rimnicu Vilcea', 97), ('Craiova', 138), ('Bucharest', 101)),
        'Bucharest': (('Pitesti', 101), ('Fagaras', 211), ('Giurgiu', 90), ('Urziceni', 85)),
        'Giurgiu': (('Bucharest', 90)),
        'Urziceni': (('Bucharest', 85), ('Hirsova', 98), ('Vaslui', 142)),
        'Hirsova': (('Urziceni', 98), ('Eforie', 86)),
        'Eforie': (('Hirsova', 86)),
        'Vaslui': (('Urziceni', 142), ('Iasi', 92)),
        'Iasi': (('Vaslui', 92), ('Neamt', 87)),
        'Neamt': (('Iasi', 87))
    }
    
    distToGoal = {
        'Arad': 366,
        'Bucharest': 0,
        'Craiova': 160,
        'Dobreta': 242,
        'Eforie': 161,
        'Fagaras': 176,
        'Giurgiu': 77,
        'Hirsova': 151,
        'Iasi': 226,
        'Lugoj': 244,
        'Mehadia': 241,
        'Neamt': 234,
        'Oradea': 380,
        'Pitesti': 100,
        'Rimnicu Vilcea': 193,
        'Sibiu': 253,
        'Timisoara': 329,
        'Urziceni': 80,
        'Vaslui': 199,
        'Zerind': 374
    }

    start = Node('Arad', 0, 'Start')

    def TSPGoalP(node):
        return node.state == 'Bucharest'
    
    def TSPSuccessors(node):
        "Generates successor cities from a current state"
        return [Node(city, node.cost + cost, node.state + ' to ' + city, node) for city, cost in neighbors[node.state]]

    def TSPHeuristic(state):
        "Uses the straight line distance to the goal which is an admissible heuristic"
        return distToGoal[state]

    st = time()
    solution = Astar(start, TSPSuccessors, TSPGoalP, TSPHeuristic)
    t = time()-st
    print "Working time: %f seconds" % t
    nodes = [n for n in solution]
    nodes.reverse()
    for n in nodes: print n
