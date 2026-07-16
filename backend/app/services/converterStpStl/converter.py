import cadquery as cq


def step_to_stl_cq(input_step: str, output_stl: str) -> None:
    result = cq.importers.importStep(input_step)
    cq.exporters.export(result, output_stl)