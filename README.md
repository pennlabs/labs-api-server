Penn Mobile Server
==================

Redis-backed caching server for the Open Data APIs.
Intended for internal use at Penn Labs to speed up queries to Open Data.

Setup
-----
* Install [redis](http://redis.io/)
* Create new virtualenv
* Install requirements using `pip install requirements.txt`
* Run mobile API server with `python runserver.py`

## Dining

### Venues
Return a list of all dining venues

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/dining/venues</code></td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>None</td>
        </tr>
    </tbody>
</table>

### Weekly Menu
Return the week's menus for the venue with venue_id

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/dining/weekly_menu/{venue_id}</code></td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>None</td>
        </tr>
    </tbody>
</table>

### Daily Menu
Return the daily menu for the venue with venue_id

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/dining/daily_menu/{venue_id}</td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>None</td>
        </tr>
    </tbody>
</table>

## Directory

### Search
Search by name in the Penn Directory

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/directory/search</td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Default</th>
                            <th>Description</th>
                            <th>Example Values</th>
                        </tr>
                    </thead>
                    <tbody>
                      <tr>
                          <td><tt>name</tt></td>
                          <td><strong>Required</strong></td>
                          <td>The name to be searched for in the directory. This value is parsed into compontent parts and searched in different reasonable configurations.</td>
                          <td><tt>Alex</tt>, <tt>John Doe</tt></td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>

#### Example

GET: `http://api.pennlabs.org:5000/directory/search?name=Alex%20Wissmann`

### Person
Return the person with person_id

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/directory/person/{person_id}</td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>None</td>
        </tr>
    </tbody>
</table>

## Registrar

### Search
Search for courses by Department, Course Number, and Section

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org:5000/registrar/search</td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>GET</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Default</th>
                            <th>Description</th>
                            <th>Example Values</th>
                        </tr>
                    </thead>
                    <tbody>
                      <tr>
                          <td><tt>q</tt></td>
                          <td><strong>Required</strong></td>
                          <td>The search query for the course.</td>
                          <td><tt>cis</tt>, <tt>cis-110</tt></td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>

#### Example

GET: `http://api.pennlabs.org:5000/registrar/search?q=cis-110`
