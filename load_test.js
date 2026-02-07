import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 100,
  duration: '30s',
};

export default function () {  // default => main func
  const params = {
    headers: { 'Cookie': 'session_id=test_secret_sid' },
  };
  const res = http.get('http://127.0.0.1:8000', params);

  check(res, {  // anonym "=>" based func, (r)==res
    'is 200': (r) => r.status === 200,
    'has user': (r) => r.body.includes('user'),
  });
}
