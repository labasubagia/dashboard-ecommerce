import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style="dark")


def create_daily_order_df(df: pd.DataFrame) -> pd.DataFrame:
    res = df.resample(rule="D", on="order_purchase_timestamp").agg(
        {"order_id": "nunique", "total_order_price": "sum"}
    )
    # monthly_orders_df.index = monthly_orders_df.index.strftime("%Y-%m")

    res = res.reset_index()
    res.rename(
        columns={"order_id": "order_count", "total_order_price": "revenue"},
        inplace=True,
    )
    return res


def create_order_per_seller_df(df: pd.DataFrame) -> pd.DataFrame:
    res = df.groupby("seller_id").agg(
        {
            "price": "sum",
            "order_id": "nunique",
        }
    )
    res = res.rename(
        columns={
            "price": "revenue",
            "order_id": "order_count",
        }
    ).sort_values(by=["revenue", "order_count"], ascending=False)

    return res


def create_rating_per_seller_df(df: pd.DataFrame) -> pd.DataFrame:
    res = (
        df[~df["review_score"].isna()]
        .groupby("seller_id")
        .agg(
            {
                "review_score": "mean",
                "order_id": "nunique",
                "price": "sum",
            }
        )
        .sort_values(by=["review_score", "price", "order_id"], ascending=False)
    )
    res.rename(
        columns={
            "review_score": "rating",
            "order_id": "order_count",
            "prince": "revenue",
        },
        inplace=True,
    )
    return res


def create_rfm_df(df: pd.DataFrame) -> pd.DataFrame:
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])

    max_date = df["order_purchase_timestamp"].max()
    df["recency"] = (max_date - df["order_purchase_timestamp"]).dt.days

    frequency = (
        df.groupby("customer_id")["order_id"].count().reset_index(name="frequency")
    )
    monetary_value = (
        df.groupby("customer_id")["total_order_price"]
        .sum()
        .reset_index(name="monetary")
    )

    rfm_df = pd.merge(frequency, monetary_value, on="customer_id")

    rfm_df = pd.merge(
        rfm_df, df[["customer_id", "recency"]], on="customer_id"
    ).sort_values(by="recency", ascending=True)
    # rfm_df['recency'] = rfm_df['recency']+1

    rfm_df.drop_duplicates(inplace=True)
    return rfm_df


all_df: pd.DataFrame = pd.read_csv("./main_data.csv")

datetime_columns = [
    "order_purchase_timestamp",
]
all_df.sort_values(by="order_purchase_timestamp", ascending=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.title("E-Commerce")
    start_date, end_date = st.date_input(  # type: ignore
        label="Time Range",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],  # type: ignore
    )  # type: ignore

main_df: pd.DataFrame = all_df[
    (all_df["order_purchase_timestamp"] >= str(start_date))
    & (all_df["order_purchase_timestamp"] <= str(end_date))
]


daily_order_df = create_daily_order_df(main_df)
order_per_seller_df = create_order_per_seller_df(main_df)
rating_seller_df = create_rating_per_seller_df(main_df)
rfm_df = create_rfm_df(main_df)


st.header("E-Commerce Dashboard :sparkles:")

st.subheader("Monthly Orders")

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_order_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_order_df.revenue.sum(), "BRL", locale="pt_BR")
    st.metric("Total Revenue", value=total_revenue)


fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_order_df["order_purchase_timestamp"],
    daily_order_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9",
)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=10)
st.pyplot(fig)


st.subheader("Best and Worst Performing Sellers")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="revenue",
    y="seller_id",
    data=order_per_seller_df.head(5),
    palette=colors,
    ax=ax[0],
)
ax[0].set_ylabel("seller id", fontsize=30)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Sellers revenue", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=35)
ax[0].tick_params(axis="x", labelsize=30)

sns.barplot(
    x="revenue",
    y="seller_id",
    data=order_per_seller_df.sort_values(by="revenue", ascending=True).head(5),
    palette=colors,
    ax=ax[1],
)
ax[1].set_ylabel("seller id", fontsize=30)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].set_title("Worst Performing Seller revenue", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=35)
ax[1].tick_params(axis="x", labelsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()

st.pyplot(fig)


st.subheader("Best and Worst Rating Sellers")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(
    x="rating",
    y="seller_id",
    data=rating_seller_df.head(5),
    palette=colors,
    ax=ax[0],
)
ax[0].set_ylabel("seller id", fontsize=30)
ax[0].set_xlabel("Rating", fontsize=30)
ax[0].set_title("Best Rating Seller", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=35)
ax[0].tick_params(axis="x", labelsize=30)

sns.barplot(
    x="rating",
    y="seller_id",
    data=rating_seller_df.sort_values(by="rating", ascending=True).head(5),
    palette=colors,
    ax=ax[1],
)
ax[1].set_ylabel("seller id", fontsize=30)
ax[1].set_xlabel("Rating", fontsize=30)
ax[1].set_title("Worst Rating Seller", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=35)
ax[1].tick_params(axis="x", labelsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()

st.pyplot(fig)

st.subheader("Seller revenue")
fig = plt.figure(figsize=(10, 6))
plt.scatter(
    order_per_seller_df["order_count"],
    order_per_seller_df["revenue"],
    marker=".",
)
plt.xlabel("Order Count")
plt.ylabel("Revenue")
plt.title("Seller performance comparison")
plt.grid(True)
st.pyplot(fig)


st.subheader("Best Customer Based on RFM Parameters")

rot = 90
x_labelsize = 25

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale="pt_BR")
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(
    y="recency",
    x="customer_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    palette=colors,
    ax=ax[0],
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis="y", labelsize=30)
ax[0].tick_params(axis="x", labelsize=x_labelsize, rotation=rot)


sns.barplot(
    y="frequency",
    x="customer_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    palette=colors,
    ax=ax[1],
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis="y", labelsize=30)
ax[1].tick_params(axis="x", labelsize=x_labelsize, rotation=rot)

sns.barplot(
    y="monetary",
    x="customer_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    palette=colors,
    ax=ax[2],
)
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis="y", labelsize=30)
ax[2].tick_params(axis="x", labelsize=x_labelsize, rotation=rot)


st.pyplot(fig)

st.caption("Copyright (c) Laba 2025")
