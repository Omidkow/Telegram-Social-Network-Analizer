from datetime import datetime, timedelta, timezone
import json
import os
import pickle
import networkx as nx

JSON_FILE_PATH = "result.json"
CACHE_FILE = "telegram_graph_7days.pkl"


def build_graph_from_json():
  G = nx.DiGraph()

  print(f"در حال خواندن فایل JSON از مسیر '{JSON_FILE_PATH}'...")
  if not os.path.exists(JSON_FILE_PATH):
    print(f"خطا: فایل {JSON_FILE_PATH} پیدا نشد!")
    return G

  with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

  messages = data.get("messages", [])
  print(f"کل پیام‌های موجود در فایل JSON: {len(messages)}")

  one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

  msg_id_to_sender = {}
  message_count = 0

  for msg in messages:
    if msg.get("type") != "message":
      continue

    msg_id = msg.get("id")
    sender_id = msg.get("from_id")
    sender_name = msg.get("from", "Unknown")

    if msg_id and sender_id:
      msg_id_to_sender[msg_id] = sender_id

      if not G.has_node(sender_id):
        G.add_node(
            sender_id,
            gender="unknown",
            is_bot=False,
            full_name=sender_name,
            user_id=sender_id,
        )

  print("در حال استخراج بازه ۷ روزه و ساخت یال‌های ریپلای...")
  for msg in messages:
    if msg.get("type") != "message":
      continue

    msg_date_str = msg.get("date")
    if not msg_date_str:
      continue

    try:
      msg_date = datetime.fromisoformat(msg_date_str).replace(
          tzinfo=timezone.utc
      )
    except Exception:
      continue

    if msg_date < one_week_ago:
      continue

    message_count += 1

    sender_id = msg.get("from_id")
    if not sender_id:
      continue

    reply_to_id = msg.get("reply_to_message_id")
    if not reply_to_id:
      continue

    target_sender_id = msg_id_to_sender.get(reply_to_id)
    if not target_sender_id or sender_id == target_sender_id:
      continue

    if G.has_edge(sender_id, target_sender_id):
      G[sender_id][target_sender_id]["weight"] += 1
    else:
      G.add_edge(sender_id, target_sender_id, weight=1)

  print(
      f"پایان پردازش! مجموع پیام‌های بررسی‌شده در ۷ روز گذشته: {message_count}"
      f" پیام"
  )

  with open(CACHE_FILE, "wb") as f:
    pickle.dump(G, f)
  print("گراف روی فایل کش ذخیره شد.")

  return G


def main():
  if os.path.exists(CACHE_FILE):
    print("بارگذاری گراف از فایل کش محلی...")
    with open(CACHE_FILE, "rb") as f:
      master_graph = pickle.load(f)
  else:
    master_graph = build_graph_from_json()

  male_identifiers = [
      "user6395990624",
      "user5142448294",
      "user7033852828",
      "user6163361048",
      "user1213345841",
      "user7180696644",
      "user1168979302",
      "user764974330",
      "user5390617224",
      "user1752692342",
      "user1389402302",
      "user5563630379",
  ]

  bot_identifiers = [
      "user8241939804",
      "user7426113253",
  ]

  for node, data in master_graph.nodes(data=True):
    if node in bot_identifiers:
      data["gender"] = "bot"
      data["is_bot"] = True
    elif node in male_identifiers:
      data["gender"] = "male"
      data["is_bot"] = False
    else:
      data["gender"] = "female"
      data["is_bot"] = False

  human_nodes = [
      n for n, d in master_graph.nodes(data=True) if not d.get("is_bot", False)
  ]
  sub_graph = master_graph.subgraph(human_nodes)

  mixing_matrix = nx.attribute_mixing_dict(sub_graph, "gender")

  print("\n--- ماتریس جریان مکالمات (Mixing Matrix) ---")
  for src in ["male", "female"]:
    for dst in ["male", "female"]:
      count = mixing_matrix.get(src, {}).get(dst, 0)
      print(f"از {src} به {dst}: {count} ریپلای")

  try:
    assortativity = nx.attribute_assortativity_coefficient(sub_graph, "gender")
    print(f"\nشاخص هم‌گروهی جنسیتی (Assortativity): {assortativity:.4f}")
  except Exception as e:
    print(f"\nخطا در محاسبه Assortativity: {e}")

  print(
      f"\nگراف آماده است! تعداد گره‌ها: {master_graph.number_of_nodes()} | تعداد"
      f" یال‌ها: {master_graph.number_of_edges()}"
  )

  if sub_graph.number_of_nodes() > 0:
    print("\n--- رتبه‌بندی کاربران بر اساس تعامل در ۷ روز گذشته ---")
    pagerank_scores = nx.pagerank(sub_graph, weight="weight")
    sorted_users = sorted(
        pagerank_scores.items(), key=lambda x: x[1], reverse=True
    )

    for rank, (user, score) in enumerate(sorted_users[:10], 1):
      user_data = master_graph.nodes[user]
      name = user_data.get("full_name", user)
      print(f"{rank}. کاربر: {name} - امتیاز: {score * 100:.4f}")

  # --- ۵ نفر برتر بر اساس نسبت جذابیت (با کف حداقل ۱۰ ریپلای دریافتی) ---
  MIN_IN_REPLIES = 100
  attraction_list = []

  for user in sub_graph.nodes():
    user_data = master_graph.nodes[user]
    name = user_data.get("full_name", user)
    gender = user_data.get("gender", "unknown")

    in_deg = sub_graph.in_degree(user, weight="weight")
    out_deg = sub_graph.out_degree(user, weight="weight")

    if in_deg >= MIN_IN_REPLIES:
      ratio = in_deg / (out_deg if out_deg > 0 else 1)
      attraction_list.append({
          "user": user,
          "name": name,
          "gender": gender,
          "in_deg": in_deg,
          "out_deg": out_deg,
          "ratio": ratio,
      })

  sorted_by_attraction = sorted(
      attraction_list, key=lambda x: x["ratio"], reverse=True
  )

  print("\n" + "=" * 55)
  print(
      f"🏆 ۵ نفر برتر در «نسبت جذابیت» (حداقل {MIN_IN_REPLIES} ریپلای دریافتی)"
  )
  print("=" * 55)

  for rank, item in enumerate(sorted_by_attraction[:5], 1):
    print(
        f"{rank}. کاربر: {item['name']}"
    )
    print(
        f"   - نسبت جذابیت (In/Out): {item['ratio']:.2f} | دریافتی (In):"
        f" {item['in_deg']} | ارسالی (Out): {item['out_deg']}"
    )
    print("-" * 55)

  # --- ۵ نفر برتر بر اساس سهم تعامل با جنس مخالف (با کف حداقل ۱۰ ریپلای ارسالی) ---
  MIN_OUT_REPLIES = 100
  cross_gender_list = []

  for user in sub_graph.nodes():
    user_data = master_graph.nodes[user]
    name = user_data.get("full_name", user)
    gender = user_data.get("gender", "unknown")

    if gender not in ["male", "female"]:
      continue

    out_deg = sub_graph.out_degree(user, weight="weight")

    if out_deg >= MIN_OUT_REPLIES:
      total_out_edges = 0
      cross_gender_edges = 0

      for _, neighbor, edge_data in sub_graph.out_edges(user, data=True):
        weight = edge_data.get("weight", 1)
        total_out_edges += weight

        neighbor_gender = sub_graph.nodes[neighbor].get("gender", "unknown")
        if neighbor_gender in ["male", "female"] and gender != neighbor_gender:
          cross_gender_edges += weight

      cross_share = (
          (cross_gender_edges / total_out_edges) * 100
          if total_out_edges > 0
          else 0
      )

      cross_gender_list.append({
          "user": user,
          "name": name,
          "gender": gender,
          "out_deg": out_deg,
          "cross_share": cross_share,
          "cross_edges": cross_gender_edges,
      })

  sorted_by_cross_share = sorted(
      cross_gender_list, key=lambda x: x["cross_share"], reverse=True
  )

  print("\n" + "=" * 55)
  print(
      "💬 ۵ نفر برتر در «تعامل با جنس مخالف» (حداقل"
      f" {MIN_OUT_REPLIES} ریپلای ارسالی)"
  )
  print("=" * 55)

  for rank, item in enumerate(sorted_by_cross_share[:5], 1):
    print(
        f"{rank}. کاربر: {item['name']}"
    )
    print(
        f"   - سهم تعامل با جنس مخالف: {item['cross_share']:.1f}% | ریپلای به"
        f" جنس مخالف: {item['cross_edges']} از {item['out_deg']}"
    )
    print("-" * 55)


if __name__ == "__main__":
  main()