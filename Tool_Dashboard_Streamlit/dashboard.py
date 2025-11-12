import streamlit as st
import pandas as pd
import os

# ---------- Configuration ----------
st.set_page_config(page_title="Tool Compatibility Dashboard", layout="wide")
DATA_DIR = "data"

st.title("🔧 Tool Compatibility Dashboard")
st.caption("Optimizes tool usage per Work Center using shared-tool matrices.")

# ---------- Check for data folder ----------
if not os.path.exists(DATA_DIR):
    st.warning("⚠️ `data/` folder not found. Upload Excel files under `data` directory.")
    st.stop()

# ---------- List Work Centers ----------
work_centers = [f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f))]
if not work_centers:
    st.warning("No Work Center folders detected in `data/`. Each must contain `Tool_Matrix.xlsx`.")
    st.stop()

work_center = st.sidebar.selectbox("Select Work Center", work_centers)

# ---------- Path to Excel ----------
excel_path = os.path.join(DATA_DIR, work_center, "Tool_Matrix.xlsx")
if not os.path.exists(excel_path):
    st.error(f"❌ {excel_path} not found. Ensure each Work Center folder contains `Tool_Matrix.xlsx`.")
    st.stop()

# ---------- Load Excel ----------
@st.cache_data
def load_matrix(path):
    return pd.read_excel(path, sheet_name=0, index_col=0)

try:
    df = load_matrix(excel_path)
except Exception as e:
    st.error(f"Error reading {excel_path}: {e}")
    st.stop()

st.success(f"✅ Loaded matrix {df.shape[0]} × {df.shape[1]}.")
st.dataframe(df)

# ---------- Sequence Optimization ----------
item_list = df.index.tolist()
st.markdown("### Sequence Optimization")
seq_items = st.multiselect("Select item numbers to sequence:", item_list, default=item_list[:5])
ref_item = st.selectbox("Reference (start) item:", item_list)

if st.button("🔁 Optimize Sequence"):
    if not seq_items or ref_item not in seq_items:
        st.warning("Please select items including the reference item.")
    else:
        remaining = [i for i in seq_items if i != ref_item]
        sequence = [ref_item]
        while remaining:
            last = sequence[-1]
            next_item = max(remaining, key=lambda x: df.loc[last, x])
            sequence.append(next_item)
            remaining.remove(next_item)

        st.markdown("#### Optimized Sequence")
        st.write(" → ".join(sequence))

        # Calculate tool metrics
        total_tools = df.loc[sequence, sequence].sum(axis=1)
        shared_tools = [df.loc[sequence[i], sequence[i + 1]] for i in range(len(sequence) - 1)]
        saved = sum(shared_tools)
        changes = len(sequence) * df.shape[1] - saved

        st.markdown("#### Tool Usage Summary")
        metrics = pd.DataFrame({"Item": sequence, "Total Tools Used": total_tools.values})
        st.dataframe(metrics)
        st.write(f"**Total Tools Saved:** {saved}")
        st.write(f"**Estimated Tool Changes Required:** {changes}")

        # Download option
        csv = metrics.to_csv(index=False)
        st.download_button("⬇️ Download Metrics as CSV", csv, "metrics.csv", "text/csv")


