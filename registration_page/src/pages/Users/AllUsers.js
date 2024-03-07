import { useState } from "react";

function AllUsers(props) {
	const [users, setUsers] = useState('');

	const handleRefresh = (e) => {
		e.preventDefault();
		const finalFormEndpoint = props["endpoint"];
		console.log(finalFormEndpoint);
		fetch(finalFormEndpoint, {
			method: 'GET',
			headers: {
				"Accept": "*/*",
			},
		})
			.then((response) => {
				if (!response.ok) {
					return alert('Something went wrong server side.');
				}
				console.log(response);
				response.json().then((data) => {
					console.log(data);
					setUsers(data);
				});
				//   return alert("Success!");
			}).catch(() => {
				return alert('Could not submit form. Please try again later. Network error likely.');
			});
	}
	return (
		<>
			<div>
				<h1>All Users</h1>
				<button onClick={handleRefresh}>Refresh</button>
			</div>
			<div>
				{users !== '' && (
				<ul>
					{users.map((item, index) => (
						<li key={index}> {item} </li>
					))}
				</ul>
				)}
			</div>
		</>
	);
}

export default AllUsers;