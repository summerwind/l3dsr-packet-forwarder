Vagrant.configure('2') do |config|
  config.vm.define "forwarder" do |host|
    host.vm.hostname = "forwarder"
    host.vm.box = "ubuntu/trusty64"
    host.vm.network :private_network, ip: "192.168.10.10"

    host.vm.provider :virtualbox do |v|
      v.name = "forwader"
      v.cpus = 1
      v.memory = 1024
    end

    host.vm.provision :shell, :privileged => true, :path => "vagrant/setup-forwarder.sh"
  end

  config.vm.define "server" do |host|
    host.vm.hostname = "server"
    host.vm.box = "ubuntu/trusty64"
    host.vm.network :private_network, ip: "192.168.10.11"

    host.vm.provider :virtualbox do |v|
      v.name = "server"
      v.cpus = 1
      v.memory = 512
    end

    host.vm.provision :shell, :privileged => true, :path => "vagrant/setup-server.sh"
  end
end
