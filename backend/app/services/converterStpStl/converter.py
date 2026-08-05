import cadquery as cq


def convert_to_stl(input_step: str, output_stl: str) -> None:
    result = cq.importers.importStep(input_step)
    cq.exporters.export(result, output_stl)