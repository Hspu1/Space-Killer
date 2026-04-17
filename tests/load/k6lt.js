import http from "k6/http";

export const options = {
  stages: [
    { duration: "5s", target: 70 },
    { duration: "20m", target: 70 },
    { duration: "5s", target: 0 },
  ],
  discardResponseBodies: true,
};

export default function () {
  const BASE_URL = "http://127.0.0.1:8000";
  const randomId = Math.floor(Math.random() * 100000000);
  const query = `id=${randomId}&first_name=Tester&auth_date=${Math.floor(Date.now() / 1000)}&hash=mock`;

  const params = {
    redirects: 0,
    headers: { Host: "127.0.0.1:8000" },
    tags: { name: "tg_callback" },
  };

  let res = http.get(`${BASE_URL}/auth/telegram/callback?${query}`, params);
}
