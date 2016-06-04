Penn Mobile Server
==================

[![Build Status](https://travis-ci.org/pennlabs/penn-mobile-server.svg?branch=master)](https://travis-ci.org/pennlabs/penn-mobile-server)

Redis-backed caching server for the Open Data APIs.
Intended for internal use at Penn Labs to speed up queries to Open Data.

Setup
-----
* Install [redis](http://redis.io/)
* Create new virtualenv
* Install requirements using `pip install -r requirements.txt`
* Run mobile API server with `python runserver.py`

## Buildings

### Search
Use a word or phrase to search for a Penn building

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/buildings/search</td>
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
                          <td>The building search query</td>
                          <td><tt>Harrison</tt>, <tt>Levine Hall</tt></td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>

### By Building Code
Return the building corresponding to the given code

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/buildings/{building_code}</code></td>
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


## Dining

### Venues
Return a list of all dining venues

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/dining/venues</code></td>
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
            <td><code>http://api.pennlabs.org/dining/weekly_menu/{venue_id}</code></td>
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
            <td><code>http://api.pennlabs.org/dining/daily_menu/{venue_id}</td>
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
            <td><code>http://api.pennlabs.org/directory/search</td>
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

GET: `http://api.pennlabs.org/directory/search?name=Alex%20Wissmann`

### Person By ID
Return the person with person_id

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/directory/person/{person_id}</td>
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
            <td><code>http://api.pennlabs.org/registrar/search</td>
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

GET: `http://api.pennlabs.org/registrar/search?q=cis-110`

## Laundry

### All Halls
Return information on all laundry rooms

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/laundry/halls</td>
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

### Hall by hall_no
Get information for a specific room by the hall_no. hall_no is given in the All Halls response.

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/laundry/hall/{hall_no}</td>
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

## Transit

### Routing
Finds a route, from all Penn Transit routes, which provides the shortest total walking distance to get from (latFrom, lonFrom) to (latTo, lonTo). If there is no path which shortens the travelers walking distance, an error is returned.

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/transit/routing</td>
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
                        </tr>
                    </thead>
                    <tbody>
                      <tr>
                          <td><tt>latFrom</tt></td>
                          <td><strong>Required</strong></td>
                          <td>Starting Latitude</td>
                      </tr>
                      <tr>
                          <td><tt>lonFrom</tt></td>
                          <td><strong>Required</strong></td>
                          <td>Starting Longitude</td>
                      </tr>
                      <tr>
                          <td><tt>latTo</tt></td>
                          <td><strong>Required</strong></td>
                          <td>Ending Latitude</td>
                      </tr>
                      <tr>
                          <td><tt>lonTo</tt></td>
                          <td><strong>Required</strong></td>
                          <td>Ending Longitude</td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>

#### Example

GET: `http://api.pennlabs.org/transit/routing?latFrom=39.9533568&lonFrom=-75.2161194&latTo=39.9495731&lonTo=-75.12924031`

### Stops
Get information on all stops

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/transit/stops</td>
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

### Routes
Get information on all routes. This has the same information as the stops endpoint, but is indexed by route.

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>http://api.pennlabs.org/transit/routes</td>
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

## Athletics

Documentation for the athletics endpoints is located at the Labs pennathletics
library SDK repository [README](https://github.com/pennlabs/pennathletics/blob/master/README.md#sports)

## Authentication

### Validate token
Validate whether token is valid. **Note**: You must access this endpoint over TLS/SSL (https).

<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>https://api.pennlabs.org/validate/{token}</td>
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
