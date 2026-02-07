import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const SESSION_ID = __ENV.SESSION_ID || '';

export const options = {
  stages: [
    { duration: '5s', target: 50 },
    { duration: '20s', target: 100 },
    { duration: '5s', target: 0 },
  ],
  thresholds: {
    'http_req_duration{type:main}': ['p(95)<250'],
    'http_req_failed': ['rate<0.01'],
    'checks': ['rate>0.99'],
  },
};

export default function () {
  const params = {
    headers: {
      'Cookie': `session_id=${SESSION_ID}`,
      'User-Agent': 'k6-load-test',
    },
    tags: { type: 'main' },
  };
  const res = http.get(`${BASE_URL}/`, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'body contains user': (r) => r.body && r.body.includes('user'),
  });
  sleep(0.001);
}
