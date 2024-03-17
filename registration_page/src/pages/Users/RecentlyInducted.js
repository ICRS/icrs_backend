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
				{users !== '' && (
				<ul>
					{users.map((item, index) => (
						<li key={index}> {item} </li>
					))}
				</ul>
				)}
			</div>
		</div>
	);
}

// export default AllUsers;