import streamlit as st
import pandas as pd
import numpy as np
import os

# === CONFIGURATION ===
DATA_DIR = "data"

st.set_page_config(page_title="Tool Compatibility Optimizer", layout="wide")
st.title("🔧 Tool Compatibility Optimizer — Numeric Dashboard")

# --- Work Center selection ---
work_centers = [f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f))]
selected_wc = st.selectbox("Select Work Center", work_centers)

if selected_wc:
    # === Load Tool Matrix ===
    path = os.path.join(DATA_DIR, selected_wc, "Tool_Matrix.xlsx")
    if not os.path.exists(path):
        st.error(f"Tool_Matrix.xlsx not found in {selected_wc}")
    else:
        df = pd.read_excel(path, sheet_name="Tool_Matrix", index_col=0)
        st.write(f"✅ Loaded matrix: **{df.shape[0]} items × {df.shape[1]} items**")

        all_items = df.index.tolist()
        selected_items = st.multiselect("Select items to include", all_items, default=all_items[:5])
        start_item = st.selectbox("Select starting item", selected_items)

        if st.button("⚙️ Optimize Sequence") and selected_items and start_item:
            # --- Subset matrix ---
            valid = [i for i in selected_items if i in df.index]
            df_sub = df.loc[valid, valid]

            # --- Optimization (Greedy) ---
            def optimize_seq(shared_df, start_item):
                remaining = list(shared_df.index)
                seq = [start_item]
                remaining.remove(start_item)
                while remaining:
                    last = seq[-1]
                    next_item = shared_df.loc[last, remaining].idxmax()
                    seq.append(next_item)
                    remaining.remove(next_item)
                return seq

            seq = optimize_seq(df_sub, start_item)

            st.subheader("🧩 Optimized Sequence")
            st.write(" → ".join(seq))

            # --- Tool totals per item ---
            tool_totals = df_sub.sum(axis=1)
            tool_table = pd.DataFrame({"Item": tool_totals.index, "Total_Tools": tool_totals.values})
            st.subheader("🧮 Total Tools per Item (in Selected Matrix)")
            st.dataframe(tool_table, use_container_width=True)

            # --- Shared tools saved per transition ---
            shared_tools = [df_sub.loc[seq[i], seq[i+1]] for i in range(len(seq) - 1)]
            total_shared = sum(shared_tools)
            total_unique = tool_totals.loc[seq].sum() - total_shared
            total_changes = len(seq) - 1

            st.subheader("📊 Summary of Sequence Efficiency")
            st.write(f"🔹 **Total Items:** {len(seq)}")
            st.write(f"🔹 **Total Tools Used (Sum of Each Item):** {tool_totals.loc[seq].sum():,.0f}")
            st.write(f"🔹 **Tools Saved (Shared between consecutive items):** {total_shared:,.0f}")
            st.write(f"🔹 **Effective Tool Changes Required:** {total_changes:,.0f}")
            st.write(f"🔹 **Adjusted Tools After Savings:** {total_unique:,.0f}")

            # --- Display final submatrix used ---
            st.subheader("📘 Sub-Matrix (Used in Optimization)")
            st.dataframe(df_sub.loc[seq, seq], use_container_width=True)

            # --- Export results to Excel ---
            out_path = os.path.join(DATA_DIR, selected_wc, "Optimization_Results.xlsx")
            with pd.ExcelWriter(out_path) as writer:
                pd.DataFrame({"Optimized_Sequence": seq}).to_excel(writer, sheet_name="Sequence", index=False)
                tool_table.to_excel(writer, sheet_name="Tool_Totals", index=False)
                df_sub.loc[seq, seq].to_excel(writer, sheet_name="Sub_Matrix")

            with open(out_path, "rb") as f:
                st.download_button("💾 Download Results Excel", f, file_name=f"{selected_wc}_Optimization_Results.xlsx")

