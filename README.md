# Installation

```
sudo apt install jq python3-gmpy2
sudo pip3 install -r requirements.txt
```

Install [inetdata](https://github.com/hdm/inetdata)


# Configuration

Configuration file must be placed in `/etc/k-reaper/config.json` and must contain the following values:

```
{
    "basedir": "/path/to/downloaded/and/parsed/data/root/directory",
    "inetdata_bin_path": "/path/to/bin/directory/of/your/inetdata/installation",
    "inetdata_data_path": "/path/to/data/directory/of/your/inetdata/installation",
    "gitlab_private_token": "your gitlab.com private token",
    "github_oauth_token": "your github.com oauth token",
    "tmp_dir": "/path/to/tmp/dir/with/enough/free/space"

}
```
