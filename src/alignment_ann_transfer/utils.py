from typing import Dict

from stam import AnnotationStore


def extract_anns(layer: AnnotationStore) -> Dict:
    """
    Extract annotation from layer(STAM)
    """
    anns = {}
    for ann in layer.annotations():
        start, end = ann.offset().begin().value(), ann.offset().end().value()
        ann_metadata = {}
        for data in ann:
            ann_metadata[data.key().id()] = str(data.value())
        anns[int(ann_metadata["root_idx_mapping"])] = {
            "Span": {"start": start, "end": end},
            "text": str(ann),
            "root_idx_mapping": int(ann_metadata["root_idx_mapping"]),
        }
    return anns
