import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '10s', target: 200 },
        { duration: '40s', target: 200 },
        { duration: '10s', target: 0 },
    ],
    discardResponseBodies: true,
};

const providers = ['github', 'yandex'];

export default function () {
    const BASE_URL = 'http://127.0.0.1:8000';
    const provider = providers[Math.floor(Math.random() * providers.length)];

    const params = {
        redirects: 0,
        headers: { 'Host': '127.0.0.1:8000' }
    };

    let loginRes = http.get(`${BASE_URL}/auth/${provider}/login`, params);
    if (loginRes.status === 429) return;

    let setCookie = loginRes.headers['Set-Cookie'];
    let location = loginRes.headers['Location'] || "";
    let stateMatch = location.match(/state=([^&]+)/);

    if (!setCookie || !stateMatch) return;
    let state = stateMatch[1];
    let cbUrl = `${BASE_URL}/auth/${provider}/callback?code=mock_code&state=${state}`;

    let cbRes = http.get(cbUrl, {
        headers: {
            'Host': '127.0.0.1:8000',
            'Cookie': setCookie.split(';')[0]
        },
        redirects: 0
    });

    if (cbRes.status !== 429) {
        check(cbRes, {
            [`${provider} status is 307`]: (r) => r.status === 307,
            [`${provider} welcome redirect`]: (r) => r.headers['Location'] && r.headers['Location'].includes('/welcome'),
        });
    }

    sleep(0.1);
}
