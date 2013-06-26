#!/usr/bin/ruby -W0
# This script is used to set/remove maintenance mode in zabbix
# you need proper permissions for login_user set in zabbix server webui
# you need gem zbxapi
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com
#
require 'zbxapi'
require 'date'

###########################################
#config starts
server = "http://monitoring.lan"
login_user = "user"
login_pass = "password"
#config ends
###########################################

def connect(server,login_user,login_pass)
    zabbix = ZabbixAPI.new(server)
    zabbix.login(login_user,login_pass)
    zabbix
end

def create_maintenance(zabbix,group_id,start_time,period,name="deploy")
    end_time = start_time + period
    result = zabbix.raw_api(
        "maintenance.create",
        {
            "groupids"=>[group_id.to_i],
            "name"=>name,
            "maintenance_type"=>"0",
            "description"=>"created by zab.rb",
            "active_since"=>start_time.to_s,
            "active_till"=>end_time.to_s,
            "timeperiods"=> [{
                "timeperiod_type"=>"0",
                "start_date"=>start_time.to_s,
                "period"=>period.to_s
            }]
        }
    )
    result["maintenanceids"]
end
def get_maintenance_ids(zabbix,group_id)
    result = zabbix.raw_api("maintenance.get","search"=>{"groupids"=>[group_id]})
    if result[0].nil?
      puts "no maintenances for group #{group_id} found!"
      exit 2
    end
    maintenance_ids = []
    result.each do |res|
        maintenance_ids << res["maintenanceid"]
    end
    maintenance_ids
end
def get_maintenances(zabbix,group_id)
    result = zabbix.raw_api("maintenance.get","output"=>"extend","search"=>{"groupids"=>[group_id]})
    if result[0].nil?
      puts "no maintenances for group #{group_id} found!"
      exit 2
    end
    formated_maintenances = []
    result.each do |res|
        end_time = DateTime.strptime(res['active_till'],'%s').to_time.to_s
        formated_maintenances << "#{res['maintenanceid']}: #{res['name']} till #{end_time}"
    end
    formated_maintenances
end
def delete_maintenance(zabbix,maintenance_ids)
    result = zabbix.raw_api("maintenance.delete",maintenance_ids)
end
def get_group_id(zabbix,group_name)
    group = zabbix.hostgroup.get({"output"=>"extend","search"=>{"name"=>group_name},"searchWildcardsEnabled"=>1})
    if group[0].nil?
      puts "group #{group_name} not found!"
      exit 2
    end
    group[0]["groupid"]
end


if ARGV[1].nil?
    puts "use #{File.basename($0)} create|delete|show group_name [period in seconds]"
    exit 1
end
group_name = ARGV[1]
action = ARGV[0]
case action
when "create"
    zabbix = connect(server,login_user,login_pass)
    now = Time.now
    start_time = now.to_i
    name = "deploy #{now.to_s}"
    period = ARGV[2].to_i
    if period.nil?
        period = 600 #10 * 60 seconds
    end
    group_id = get_group_id(zabbix,group_name)
    maintenance_ids = create_maintenance(zabbix,group_id,start_time,period,name)
    puts "done"
    exit 0
when "delete"
    zabbix = connect(server,login_user,login_pass)
    group_id = get_group_id(zabbix,group_name)
    maintenance_ids = get_maintenance_ids(zabbix,group_id)
    delete_maintenance(zabbix,maintenance_ids)
    puts "done"
    exit 0
when "show"
    zabbix = connect(server,login_user,login_pass)
    group_id = get_group_id(zabbix,group_name)
    maintenances = get_maintenances(zabbix,group_id)
    maintenances.each do |m|
      puts m
    end
else
    puts "Wrong action #{action}"
end
