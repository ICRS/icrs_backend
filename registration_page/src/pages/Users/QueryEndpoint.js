import { useState } from "react";

export default function QueryEndpoint(endpoint, request_method) {
	const [users, setUsers] = useState('');

	const handleRefresh = (e) => {
		e.preventDefault();

		fetch(endpoint, {
			method: request_method,
			headers: {
				"Accept": "*/*",
			},
		})
			.then((response) => {
				if (!response.ok) {
					return alert('Something went wrong server side.');
				}

				response.json().then((data) => {
					console.log(data)
					console.log(data[0])
					console.log(data[1])
					setUsers(data);
				});
			}).catch(() => {
				return alert('Could not submit form. Please try again later. Network error likely.');
			});
	}
	return { handleRefresh, users };
}
