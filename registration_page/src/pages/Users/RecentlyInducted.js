import QueryEndpoint from "./QueryEndpoint";

export default function RecentlyInducted(props) {
	const { handleRefresh, users } = QueryEndpoint(props["endpoint"], "GET");

	const handleRegisterUsers = () => {
		fetch(props["registrationEndpoint"], {
			method: "GET",
			headers: {
				"Accept": "*/*",
			},
		})
			.then((response) => {
				if (!response.ok) {
					return alert('Something went wrong server side.');
				}
			}).catch(() => {
				return alert('Something went wrong. Please try again later. Network error likely.');
			});

	}

	return (
		<div className="form-box">
			<div>
				<h1>Recently Inducted Users</h1>
				<p>Get list of users to send to card office</p>
				<button onClick={handleRefresh}> Refresh </button>
				<button onClick={handleRegisterUsers}> Update Registered Users </button>
			</div>
			<div >
				{users !== '' && users[0] !== '' && (
					<div>
						<br />
						<h3> Previously Inducted </h3>
						<ul>
							{users[0].map((item, index) => (
								<li key={index}> {item} </li>
							))}
						</ul>
					</div>
				)}
				{users !== '' && users[1] !== '' && (
					<div>
						<br />
						<h3> Previously Inducted </h3>
						<ul>
							{users[1].map((item, index) => (
								<li key={index}> {item.join(", ")} </li>
							))}
						</ul>
					</div>
				)}
			</div>
		</div>
	);
}

// export default AllUsers;