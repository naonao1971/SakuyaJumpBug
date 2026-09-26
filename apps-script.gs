/**
 * 咲耶ジャンプバグ ランキング用 Google Apps Script (Web App)
 * 作りは姉妹作「咲耶Nounラリー」の apps-script.gs と同じ。列の中身だけこの作品に合わせてある。
 *
 * セットアップ手順:
 * 1. 記録用のスプレッドシート「score3」を開く（空のままでよい）
 * 2. 拡張機能 → Apps Script を開き、このファイルの内容を貼り付けて保存
 * 3. 「デプロイ」→「新しいデプロイ」→種類「ウェブアプリ」を選択
 *    - 実行するユーザー: 自分
 *    - アクセスできるユーザー: 全員
 * 4. 発行される URL（https://script.google.com/macros/s/.../exec）を
 *    index.html の GAS_URL 定数にセットする
 *
 * シート名（ranking）も見出し行もこのスクリプトが自動で作るので、事前の準備は要らない。
 *
 * ※ 咲耶スクランブル・咲耶Nounラリーとは別のスプレッドシートにすること。
 *   列の中身が違うので、混ぜると読めなくなる。GAS を共用にすると、再デプロイしたときに
 *   稼働中の姉妹作のランキングまで巻き込んで壊す。
 *
 * スプレッドシートの列（1レコード = 1行）:
 *   スコア | ニックネーム | X ID | 登録日時 | 端末 | 進行度 | 回収CNP | クリア
 *
 *   進行度  … コースのどこまで進んだか（0〜100 の整数。ゴールしたら 100）
 *   回収CNP … そのプレイで拾った CNP の数（0〜11）
 *   クリア  … ゴールの鳥居までたどり着いたか（"はい" / "いいえ"）
 */

const SHEET_NAME = "ranking";
const MAX_RECORDS_RETURNED = 100; // 取得件数の上限（フロント側で TOP10 に絞る）
const HEADERS = ["スコア", "ニックネーム", "X ID", "登録日時", "端末", "進行度", "回収CNP", "クリア"];

// ミスせず全部取って全部倒したときの理論値は約 28,000 点
//   コイン 105枚×50 = 5,250 / CNP 11体 = 4,100 / 敵 25体（踏むと300、忍者は撃って200）= 7,200
//   手裏剣を撃ち落とす 50点ずつ（忍者が画面にいる間だけ飛んでくる）≒ 600
//   ゴールのボーナス（燃料 最大2,000 + 残機×1,000 + CNP全員 5,000）≒ 11,000
// ミスして戻ると、戻った先の敵が復活してもう一度倒せる。その分の余裕を見て 60,000。
// それを超える値は改ざんとみなして切り詰める。
// ※ クライアント側の数字は信用できない。ここが最後の砦。
const MAX_SCORE = 60000;
const MAX_CNP = 11;

function getSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADERS);
    return sheet;
  }
  // 既存シートの見出しが足りない場合だけ補う（何か入っていれば触らない）
  const lastCol = sheet.getLastColumn();
  if (lastCol < HEADERS.length) {
    for (let c = lastCol + 1; c <= HEADERS.length; c++) {
      const cell = sheet.getRange(1, c);
      if (!String(cell.getValue() || "").trim()) cell.setValue(HEADERS[c - 1]);
    }
  }
  return sheet;
}

function doGet(e) {
  const sheet = getSheet_();
  const values = sheet.getDataRange().getValues();
  const rows = values.slice(1); // 見出し行を除く

  const records = rows
    .filter(function (r) {
      return r[1] !== "" && r[1] != null; // ニックネームが空の行は除外
    })
    .map(function (r) {
      return {
        score: Number(r[0] || 0),
        nickname: String(r[1] || ""),
        xid: String(r[2] || ""),
        created: r[3] ? new Date(r[3]).getTime() : null,
        device: String(r[4] || ""),
        progress: Number(r[5] || 0),
        cnp: Number(r[6] || 0),
        cleared: String(r[7] || "") === "はい"
      };
    })
    .sort(function (a, b) {
      return b.score - a.score;
    })
    .slice(0, MAX_RECORDS_RETURNED);

  return jsonOut_({ records: records });
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);

    if (body.action === "add") {
      const rec = body.record || {};
      const nickname = String(rec.nickname || "").trim().slice(0, 20);
      const xid = String(rec.xid || "").replace(/^@/, "").trim().slice(0, 20);
      const created = rec.created || Date.now();
      const device = String(rec.device || "").trim().slice(0, 20);

      if (!nickname) {
        return jsonOut_({ success: false, error: "nickname is required" });
      }

      // 数値はすべてここで丸める。範囲外は弾くのではなく切り詰める
      // （弾くと「登録できない」としか見えず、原因が伝わらない）
      const score = clampInt_(rec.score, 0, MAX_SCORE);
      const progress = clampInt_(rec.progress, 0, 100);
      const cnp = clampInt_(rec.cnp, 0, MAX_CNP);
      const cleared = rec.cleared === true ? "はい" : "いいえ";

      const sheet = getSheet_();
      sheet.appendRow([score, nickname, xid, new Date(created), device, progress, cnp, cleared]);
      return jsonOut_({ success: true });
    }

    return jsonOut_({ success: false, error: "unknown action" });
  } catch (err) {
    return jsonOut_({ success: false, error: String(err) });
  }
}

function clampInt_(v, lo, hi) {
  const n = Math.floor(Number(v));
  if (!isFinite(n)) return lo;
  return Math.min(hi, Math.max(lo, n));
}

function jsonOut_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
