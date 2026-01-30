def apply_step(row):
    vs = st.session_state.valve_states
    vs.clear()

    cell_p = csv_val(row, "TST_CellPresDemand")
    nde_p  = csv_val(row, "TST_InterBPDemand_NDE")
    de_p   = csv_val(row, "TST_InterBPDemand_DE")
    gas_p  = csv_val(row, "TST_GasInjectionDemand")

    # ----------------------------
    # CELL PRESSURE SELECTION
    # ----------------------------
    if cell_p > 0:
        if cell_p <= 7:
            vs["V-108"] = True
        elif cell_p <= 100:
            vs["V-107"] = True
        else:
            vs["V-106"] = True
        vs["cell"] = True

    # ----------------------------
    # INTERSPACE PRESSURE SELECTION
    # ----------------------------
    inter_p = max(nde_p, de_p)
    interspace_active = inter_p > 0

    if interspace_active:
        if inter_p <= 7:
            vs["V-111"] = True          # low
        elif inter_p <= 100:
            vs["V-110"] = True          # medium
        else:
            vs["V-109"] = True          # high

        # Enable interspace feeds
        vs["V-112"] = True              # NDE interspace enable
        vs["V-113"] = True              # DE interspace enable

    # ----------------------------
    # POD SIDE
    # ----------------------------
    if nde_p > 0:
        vs["NDE in"] = True
    if de_p > 0:
        vs["DE in"] = True

    # ----------------------------
    # RETURN + GAS INJECTION LOGIC
    # ----------------------------
    gas_active = gas_p > 0

    if interspace_active:
        # Always feed return when interspace exists
        vs["V-115"] = True              # NDE return feed
        vs["V-116"] = True              # DE return feed

        if gas_active:
            # Gas injection overrides return routing
            vs["V-206"] = True
            vs["V-207"] = True
            # V-204 / V-208 CLOSED implicitly by not setting them
        else:
            # Normal return path
            vs["V-204"] = True
            vs["V-208"] = True
