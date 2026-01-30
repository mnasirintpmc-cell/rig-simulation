def apply_dgs_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    # -------------------------------
    # CELL PRESSURE SELECTION
    # -------------------------------
    cell_p = csv_val(row, "TST_CellPresDemand")

    if cell_p > 0:
        if cell_p <= 10:
            vs["V-108"] = True          # low pressure
        elif cell_p <= 100:
            vs["V-107"] = True          # medium pressure
        else:
            vs["V-106"] = True          # high pressure

    cell_active = cell_p > 0

    # -------------------------------
    # INTERSPACE PRESSURE SELECTION
    # -------------------------------
    nde_p = csv_val(row, "TST_InterBPDemand_NDE")
    de_p  = csv_val(row, "TST_InterBPDemand_DE")

    inter_p = max(nde_p, de_p)

    if inter_p > 0:
        if inter_p <= 7:
            vs["V-111"] = True          # low pressure 0–7 bar
        elif inter_p <= 100:
            vs["V-110"] = True          # medium pressure 7–100 bar
        else:
            vs["V-109"] = True          # high pressure 100–450 bar

    nde = nde_p > 0
    de  = de_p > 0

    if nde:
        vs["V-112"] = True              # NDE interspace enable
    if de:
        vs["V-113"] = True              # DE interspace enable

    # -------------------------------
    # GAS INJECTION OVERRIDE
    # -------------------------------
    gas = csv_val(row, "TST_GasInjectionDemand") > 0

    if gas:
        # Gas injection valves
        vs["V-206"] = True
        vs["V-207"] = True

        # Feed interspaces back into pod
        vs["V-115"] = True
        vs["V-116"] = True

        nde = True
        de = True
    else:
        # Normal back-pressure mode
        if nde:
            vs["V-115"] = True
            vs["V-204"] = True

        if de:
            vs["V-116"] = True
            vs["V-208"] = True

    # -------------------------------
    # DGS POD VALVES
    # -------------------------------
    if cell_active:
        vs["cell"] = True
    if nde:
        vs["NDE in"] = True
    if de:
        vs["DE in"] = True
