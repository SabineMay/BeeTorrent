from Bee import *
from operator import itemgetter

# Returns list of tuples (piece index, number of peers who have it) 
# Sorted in reverse order so driver can got front to back in terms of requests
def get_rarest_list(swarm):
    num_pieces = len(swarm[0].bitfield)
    print(num_pieces)
    peers_have = [0] * num_pieces

    for bee in swarm:
        i = 0
        while i < num_pieces:
            if (bee.bitfield[i]):
                peers_have[i] += 1
            i += 1

    comb_list = []
    i = 0
    while i < num_pieces:
        comb_list.append((i, peers_have[i]))
        i += 1


    comb_list.sort(key=itemgetter(1))

    return comb_list
