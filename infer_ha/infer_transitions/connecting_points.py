"""
Connecting points for inferring transitions
"""
from infer_ha.clustering.utils import create_simple_modes_positions
from infer_ha.segmentation.segmentation import Segment
from infer_ha.types import Span, ConnectionPoint, Connection

def create_connecting_points(P_modes : list[list[Segment]],
                             segmentedTrajectories : list[list[Span]]) -> list[Connection]:
    """
    Determine connecting points from the segmented trajectories concerning clusters. Our idea is to establish
    connections by determining segments' start and end positions/points on either mode (src and dest modes). We plan to
    use these points to determine assignments and guards between the modes. 'datapoints' is a list of points that
    connect a source and destination location. We consider the 'datapoints' as a triplet of type
    [pre_end_posi, end_posi, start_posi], where pre_end_posi and end_posi positions are on the source location, and
    start_posi is the position of the starting point of a segment in the destination location.

    :param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
          Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
          of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
    :param position: is a list of position data structure. Each position is a pair (start, end) position of a trajectory.
        For instance, the first item of the list [0, 100] means that the trajectory has 101 points.
        The second item as [101, 300], meaning the second trajectory has 200 points.
        Note that all the trajectories are concatenated.
    :param segmentedTrajectories: is a data structure containing the positions of the segmented trajectories that keeps
        track of the connections between them.
    :return: 'datapoints' is a list of data points that holds a connection between a source and destination location.
        The 'datapoints' is a triplet of type [pre_end_posi, end_posi, start_posi], where pre_end_posi and end_posi
        positions are on the source location, and start_posi is the position of the starting point of a segment in the
        destination location.

    """

    cluster_len = len(P_modes)
    traj_size = len(segmentedTrajectories)

    mode_spans : list[list[Span]] = create_simple_modes_positions(P_modes)

    def spans_contain(spans : list[Span], x : int) -> bool:
        return any(span.start <= x <= span.end for span in spans)

    # Below computes connecting points when the number of clusters > 1. But not for single mode system
    connections : list[Connection] = []  # Structure containing [src, dest, list of connecting-points]
    for i in range(0, cluster_len):
        for j in range(i, cluster_len):  # modified j in range(i, cluster_len) from i+1
            # Code for Forward-Transitions
            links = []
            for t in range(0, traj_size):  # Loop for all trajectories
                segment_size = len(segmentedTrajectories[t])  # total number of segments in each trajectory
                for g in range(0, segment_size - 1):
                    # last start-point is compared with previous end-point
                    end_posi : int = segmentedTrajectories[t][g].end  # the end-pt of the trajectory t and segment g
                    pre_end_posi = end_posi - 1
                    if spans_contain(mode_spans[i], end_posi):  # TRUE
                        start_posi = segmentedTrajectories[t][g + 1].start  # the start-pt of the trajectory t and segment g+1
                        if spans_contain(mode_spans[j], start_posi):  # if this also returns TRUE
                            # print ("Store. (end,start)=(", end_posi,",",start_posi,") in transition(i,j)=(", i, ",",j,") \n")
                            # connections.append([i, j, [end_posi, start_posi]])
                            # Now we apppend 3 points, links.append([end_posi, start_posi])
                            links.append(ConnectionPoint(end_posi, start_posi))
            if len(links) > 0:
                connections.append(Connection(i, j, links))
                # print("[src, dest, total-points] = [", i, " , ", j, " , ", len(links), "]")

            # Code for Backward-Transitions
            if i != j:  # loop is to be done only one
                links = []
                for t in range(0, traj_size):  # Loop for all trajectories
                    segment_size = len(segmentedTrajectories[t])  # Length of each segmented trajectory
                    for g in range(0, segment_size - 1):  # last start-point is compared with previous end-point
                        end_posi = segmentedTrajectories[t][g].end
                        pre_end_posi = end_posi - 1
                        if spans_contain(mode_spans[j], end_posi):  # TRUE
                            start_posi = segmentedTrajectories[t][g + 1].start
                            if spans_contain(mode_spans[i], start_posi):  # if this also returns TRUE
                                # print("Store. (end,start)=(", end_posi, ",", start_posi,") in transition(j,i)=(", j, ",", i, ") \n")
                                # connections.append([j, i, [end_posi, start_posi]])
                                # now we have 3points: links.append([end_posi, start_posi])
                                links.append(ConnectionPoint(end_posi, start_posi))
                if len(links) > 0:
                    connections.append(Connection(j, i, links))
                    # print("[src, dest, total-points] = [", j, " , ", i, " , ", len(links), "]")
    # print("\nLength of data points = ", len(connections))
    # print("data points are ", connections)
    return connections
