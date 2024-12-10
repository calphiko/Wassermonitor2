async function getData() {
    const url = 'http://127.0.0.1:8012/get_latest/';
    const token = 'secret_token'

    try {
        const response = await fetch( url, {
            method:'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type':'application/json',
            }
        });
        if (!response.ok) {
            throw new Error('Invalid network repsonse!');
        }
        const data = await response.json()
        console.log(data);

    } catch (error) {
        console.error('There was an error with fetch-operation', error)
    }
}

window.getData = getData;