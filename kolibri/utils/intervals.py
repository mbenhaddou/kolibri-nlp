from kolibri.utils import overlap

def add_not_overlapping_entities(first_list, second_list):

    first_list = sorted(first_list, key=lambda k: k.start)
    second_list = sorted(second_list, key=lambda k: k.start)
    if len(first_list)==0:
        return second_list
    if len(second_list)==0:
        return first_list

    for ent in second_list:
        if not has_overlap(ent.start, ent.end, first_list):
            first_list.append(ent)

    return first_list

def has_overlap(start, end, list):
    for r in list:
        if overlap(start, end, r.start, r.end):
            return True
    return False